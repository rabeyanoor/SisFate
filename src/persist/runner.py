"""Shared experiment loop: load the processed object, run models over splits, log metrics + predictions."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import anndata as ad
import numpy as np
import pandas as pd
import torch

from . import graph as graph_mod
from .labels import shuffle_labels_by_group, sister_pairs
from .metrics import evaluate
from .models import baselines
from .models.contrastive import pretrain_encoder
from .models.gnn import predict, to_torch_sparse, train_gnn
from .splits import Split, inner_validation
from .utils import append_results


def processed_path(cfg: dict, cc_mode: str | None = None) -> Path:
    cc_mode = cc_mode or cfg["preprocess"]["cc_mode"]
    return Path(cfg["paths"]["processed_dir"]) / f"pre_{cc_mode}.h5ad"


@dataclass
class Context:
    """Everything a model needs, computed once per processed object."""
    adata: ad.AnnData
    cfg: dict
    obs: pd.DataFrame = field(init=False)
    y: np.ndarray = field(init=False)
    groups: np.ndarray = field(init=False)
    samples: np.ndarray = field(init=False)
    feats: dict = field(init=False, default_factory=dict)
    _A = None

    def __post_init__(self):
        self.obs = self.adata.obs
        self.y = self.obs["y"].to_numpy().astype(int)
        self.groups = self.obs["lineage_group"].to_numpy()
        self.samples = self.obs["sample"].astype(str).to_numpy()
        self.feats = {
            "pca": self.adata.obsm["X_pca"],
            "hvg": self.adata.obsm["X_hvg"],
            "cov": baselines.covariate_matrix(self.obs),
        }

    @property
    def A(self):
        if self._A is None:
            g = self.cfg["graph"]
            self._A = graph_mod.knn_graph(self.feats["pca"], self.samples, g["k"], g["metric"], g["within_sample"])
        return self._A

    def features(self, name: str) -> np.ndarray:
        if name == "pca_smooth" and name not in self.feats:
            self.feats[name] = graph_mod.smooth(self.feats["pca"], self.A, self.cfg["baselines"]["knn_smooth_alpha"])
        if name == "pca+cov" and name not in self.feats:
            self.feats[name] = np.hstack([self.feats["pca"], self.feats["cov"]])
        return self.feats[name]


def load_context(cfg: dict, cc_mode: str | None = None) -> Context:
    return Context(ad.read_h5ad(processed_path(cfg, cc_mode)), cfg)


# ---------------------------------------------------------------- model zoo
# Each model: fn(ctx, split, y_train, seed) -> scores for split.test_idx

def _sk(features: str, kind: str):
    def fn(ctx: Context, sp: Split, y_tr: np.ndarray, seed: int):
        X = ctx.features(features)
        if kind == "logreg":
            s, _ = baselines.logistic(X[sp.train_idx], y_tr, X[sp.test_idx], ctx.cfg["baselines"]["logistic_C"], seed)
        else:
            s, _ = baselines.catboost(X[sp.train_idx], y_tr, X[sp.test_idx], ctx.cfg["baselines"]["catboost"], seed)
        return s
    fn.features = features
    return fn


def _gnn(n_layers: int, pretrain: bool):
    def fn(ctx: Context, sp: Split, y_tr: np.ndarray, seed: int):
        # The graph has no cross-sample edges, so only the samples in this split matter: train on that
        # subgraph (unlabelled cells of those samples stay in as message-passing nodes).
        used = np.unique(ctx.samples[np.concatenate([sp.train_idx, sp.test_idx])])
        nodes = np.flatnonzero(np.isin(ctx.samples, used))
        local = np.full(len(ctx.y), -1)
        local[nodes] = np.arange(len(nodes))
        X_all = torch.from_numpy(ctx.features("pca"))
        X = X_all[torch.from_numpy(nodes)]
        A = to_torch_sparse(ctx.A[nodes][:, nodes]) if n_layers > 0 else None
        y = np.full(len(nodes), -1)
        y[local[sp.train_idx]] = y_tr
        tr, va = inner_validation(ctx.obs, sp.train_idx, ctx.cfg["gnn"]["val_fraction"], seed)
        enc = None
        if pretrain:
            # sister pairs from every pre-treatment sample (all arms), excluding any cell in this test set
            allowed = np.ones(len(ctx.y), bool)
            allowed[sp.test_idx] = False
            pairs = sister_pairs(ctx.obs, allowed)
            enc = pretrain_encoder(X_all, pairs, np.flatnonzero(allowed), ctx.cfg, seed)
        model = train_gnn(X, A, y, local[tr], local[va], ctx.cfg, seed, n_layers, enc)
        return predict(model, X, A, local[sp.test_idx])
    fn.features = "pca"
    return fn


def _pooled_logreg():
    """PCA-logistic trained on this split's training cells plus every labelled cell of the other arms.

    The Control-transfer results show the signal is largely shared across arms, so borrowing the
    other arms' labels should help. Cells of the test arm never enter through the pool.
    """
    def fn(ctx: Context, sp: Split, y_tr: np.ndarray, seed: int):
        X = ctx.features("pca")
        test_arms = np.unique(ctx.obs["arm"].to_numpy()[sp.test_idx])
        extra = np.flatnonzero(ctx.obs["labeled"].to_numpy() & ~ctx.obs["arm"].isin(test_arms).to_numpy())
        extra = np.setdiff1d(extra, sp.train_idx)
        y_extra = ctx.y[extra]
        if not np.array_equal(y_tr, ctx.y[sp.train_idx]):  # shuffled control: shuffle the pool too
            rng = np.random.default_rng(seed + 7919)
            y_extra = shuffle_labels_by_group(y_extra, ctx.groups[extra], ctx.samples[extra], rng)
        tr = np.concatenate([sp.train_idx, extra])
        s, _ = baselines.logistic(X[tr], np.concatenate([y_tr, y_extra]), X[sp.test_idx],
                                  ctx.cfg["baselines"]["logistic_C"], seed)
        return s
    fn.features = "pca"
    return fn


def _tuned_logreg():
    """PCA-logistic with (C, number of PCs) chosen by lineage-grouped inner CV on the training cells."""
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedGroupKFold

    grid_c = [0.005, 0.02, 0.05, 0.2, 1.0]
    grid_k = [10, 20, 30, 50]

    def fn(ctx: Context, sp: Split, y_tr: np.ndarray, seed: int):
        X = ctx.features("pca")
        Xtr, g = X[sp.train_idx], ctx.groups[sp.train_idx]
        inner = list(StratifiedGroupKFold(3, shuffle=True, random_state=seed).split(Xtr, y_tr, g))
        best, best_auc = None, -1.0
        for k in grid_k:
            for c in grid_c:
                aucs = [roc_auc_score(y_tr[te], baselines.logistic(Xtr[tr][:, :k], y_tr[tr], Xtr[te][:, :k], c, seed)[0])
                        for tr, te in inner]
                if np.mean(aucs) > best_auc:
                    best, best_auc = (k, c), float(np.mean(aucs))
        k, c = best
        s, _ = baselines.logistic(Xtr[:, :k], y_tr, X[sp.test_idx][:, :k], c, seed)
        return s
    fn.features = "pca"
    return fn


MODELS: dict[str, Callable] = {
    "pca_logreg_pooled": _pooled_logreg(),
    "pca_logreg_tuned": _tuned_logreg(),
    "cov_logreg": _sk("cov", "logreg"),
    "pca_logreg": _sk("pca", "logreg"),
    "hvg_logreg": _sk("hvg", "logreg"),
    "pca_smooth_logreg": _sk("pca_smooth", "logreg"),
    "pca_catboost": _sk("pca+cov", "catboost"),
    "hvg_catboost": _sk("hvg", "catboost"),
    "mlp": _gnn(0, False),
    "mlp_pretrain": _gnn(0, True),
}


def get_model(name: str, cfg: dict):
    if name in ("persist_gnn", "persist_gnn_nopretrain"):
        return _gnn(cfg["gnn"]["n_layers"], name == "persist_gnn")
    return MODELS[name]


# ---------------------------------------------------------------- loop

def run_models(ctx: Context, model_names: list[str], splits: list[Split], seeds: list[int],
               n_shuffles: int, experiment: str, log) -> pd.DataFrame:
    cfg = ctx.cfg
    cc_mode = ctx.adata.uns.get("cc_mode", "?")
    preds, rows = [], []
    rng = np.random.default_rng(cfg["seed"])
    for name in model_names:
        fn = get_model(name, cfg)
        for sp in splits:
            y_true_tr = ctx.y[sp.train_idx]
            variants = [(0, y_true_tr)] + [
                (k + 1, shuffle_labels_by_group(y_true_tr, ctx.groups[sp.train_idx], ctx.samples[sp.train_idx], rng))
                for k in range(n_shuffles)
            ]
            for rep, y_tr in variants:
                shuffled = rep > 0
                for seed in seeds:
                    s = fn(ctx, sp, y_tr, seed)
                    preds.append(pd.DataFrame({
                        "cell": ctx.obs.index[sp.test_idx], "model": name, "split": sp.split, "train": sp.train, "test": sp.test, "fold": sp.fold,
                        "seed": seed, "shuffled": shuffled, "shuffle_rep": rep, "y": ctx.y[sp.test_idx], "score": s,
                    }))
                    if sp.split != "within":  # within-arm folds are scored after pooling (below)
                        m = evaluate(ctx.y[sp.test_idx], s, ctx.groups[sp.test_idx],
                                     ctx.obs["state_cluster"].to_numpy()[sp.test_idx],
                                     n_boot=0 if shuffled else 500, seed=seed)
                        rows.append(dict(experiment=experiment, model=name, features=fn.features, cc_mode=cc_mode,
                                         split=sp.split, train=sp.train, test=sp.test, fold=sp.fold, seed=seed,
                                         shuffled=shuffled, notes=f"shuffle_rep={rep}" if shuffled else "", **m))
            log.info(f"{name:24s} {sp.tag:40s} done")
    P = pd.concat(preds, ignore_index=True)

    # within-arm CV is scored on pooled out-of-fold predictions (one row per arm/seed/shuffle replicate)
    W = P[P["split"] == "within"]
    for (name, arm, seed, rep), d in W.groupby(["model", "train", "seed", "shuffle_rep"]):
        idx = ctx.obs.index.get_indexer(d["cell"])
        shuffled = rep > 0
        m = evaluate(d["y"].to_numpy(), d["score"].to_numpy(), ctx.groups[idx],
                     ctx.obs["state_cluster"].to_numpy()[idx], n_boot=0 if shuffled else 500, seed=seed)
        rows.append(dict(experiment=experiment, model=name, features=get_model(name, cfg).features,
                         cc_mode=cc_mode, split="within", train=arm, test=arm, fold="oof", seed=seed,
                         shuffled=shuffled, notes=f"shuffle_rep={rep}" if shuffled else "", **m))
    append_results(rows, cfg)
    out = Path(cfg["paths"]["results_dir"]) / "preds"
    out.mkdir(exist_ok=True)
    # one file per (split kind, model) so later runs of other models or splits never overwrite it
    for (kind, model), d in P.groupby(["split", "model"]):
        d.to_csv(out / f"{experiment}_{cc_mode}_{kind}_{model}.csv.gz", index=False)
    return pd.DataFrame(rows)


def cli(experiment: str, default_models: list[str], default_seeds: list[int] | None = None) -> pd.DataFrame:
    """Shared command line for scripts/04_baselines.py and scripts/05_gnn.py."""
    import argparse

    from .splits import all_splits
    from .utils import get_logger, load_config, set_seed

    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--models", nargs="+", default=default_models)
    ap.add_argument("--splits", nargs="+", default=["within", "rep_holdout", "cross_arm"])
    ap.add_argument("--arms", nargs="+", help="restrict within/rep_holdout splits to these arms")
    ap.add_argument("--cc-mode", choices=["keep", "regress", "regress_all"])
    ap.add_argument("--n-shuffles", type=int)
    ap.add_argument("--seeds", type=int, nargs="+")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.arms:
        cfg["data"]["arms"] = args.arms
    set_seed(cfg["seed"])
    log = get_logger(experiment)
    ctx = load_context(cfg, args.cc_mode)
    splits = all_splits(ctx.obs, cfg, args.splits)
    seeds = args.seeds or default_seeds or [cfg["seed"]]
    n_shuf = cfg["splits"]["n_shuffles"] if args.n_shuffles is None else args.n_shuffles
    log.info(f"{len(splits)} splits x {len(args.models)} models x {len(seeds)} seeds x (1+{n_shuf}) label sets")
    res = run_models(ctx, args.models, splits, seeds, n_shuf, experiment, log)
    real = res[~res["shuffled"].astype(bool)]
    shuf = res[res["shuffled"].astype(bool)]
    keys = ["model", "split", "train", "test"]
    summ = real.groupby(keys)[["auroc", "auprc", "prevalence", "within_cluster_auroc"]].mean()
    summ = summ.join(shuf.groupby(keys)[["auroc", "auprc"]].mean().add_suffix("_shuffled"))
    print(summ.round(3).to_string())
    return res
