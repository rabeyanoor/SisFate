"""One-at-a-time hyperparameter sweep of the graph network around the default configuration.

Within-arm lineage-grouped CV, pooled out-of-fold AUROC, one seed per configuration. Results go to
results/gnn_sweep.csv only (results.csv and the paper figures are untouched).
"""
import argparse
import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.runner import _gnn, load_context  # noqa: E402
from persist.splits import within_arm  # noqa: E402
from persist.utils import get_logger, load_config, set_seed  # noqa: E402

# (name, section, key, value, pretrain); the default config is included as "default"
SWEEP = [
    ("default", None, None, None, False),
    ("layers=1", "gnn", "n_layers", 1, False),
    ("layers=3", "gnn", "n_layers", 3, False),
    ("hidden=64", "gnn", "hidden", 64, False),
    ("hidden=256", "gnn", "hidden", 256, False),
    ("dropout=0.1", "gnn", "dropout", 0.1, False),
    ("dropout=0.5", "gnn", "dropout", 0.5, False),
    ("lr=3e-4", "gnn", "lr", 3e-4, False),
    ("lr=3e-3", "gnn", "lr", 3e-3, False),
    ("weight_decay=1e-3", "gnn", "weight_decay", 1e-3, False),
    ("k=5", "graph", "k", 5, False),
    ("k=30", "graph", "k", 30, False),
    ("default+pretrain", None, None, None, True),
    ("temperature=0.05+pretrain", "contrastive", "temperature", 0.05, True),
    ("temperature=0.5+pretrain", "contrastive", "temperature", 0.5, True),
]

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--only", nargs="+", help="run only these configuration names")
args = ap.parse_args()
base_cfg = load_config(args.config)
log = get_logger("gnn_sweep")
ctx = load_context(base_cfg, "keep")
out = Path(base_cfg["paths"]["results_dir"]) / "gnn_sweep.csv"
done = set(pd.read_csv(out)["config"]) if out.exists() else set()
seed = base_cfg["seed"]

for name, section, key, value, pretrain in SWEEP:
    if (args.only and name not in args.only) or name in done:
        continue
    cfg = copy.deepcopy(base_cfg)
    if section:
        cfg[section][key] = value
    ctx.cfg = cfg
    ctx._A = None  # rebuild the graph if k changed
    set_seed(seed)
    fn = _gnn(cfg["gnn"]["n_layers"], pretrain)
    rows = []
    for arm in cfg["data"]["arms"]:
        idx, sc = [], []
        for sp in within_arm(ctx.obs, arm, cfg["splits"]["n_folds"], seed):
            sc.append(fn(ctx, sp, ctx.y[sp.train_idx], seed))
            idx.append(sp.test_idx)
        idx = np.concatenate(idx)
        auc = roc_auc_score(ctx.y[idx], np.concatenate(sc))
        rows.append({"config": name, "arm": arm, "pretrain": pretrain, "n_layers": cfg["gnn"]["n_layers"],
                     "hidden": cfg["gnn"]["hidden"], "dropout": cfg["gnn"]["dropout"], "lr": cfg["gnn"]["lr"],
                     "weight_decay": cfg["gnn"]["weight_decay"], "k": cfg["graph"]["k"],
                     "temperature": cfg["contrastive"]["temperature"], "seed": seed, "auroc": auc})
        log.info(f"{name:28s} {arm:12s} AUROC {auc:.3f}")
    pd.DataFrame(rows).to_csv(out, mode="a", header=not out.exists(), index=False)
ctx.cfg = base_cfg

d = pd.read_csv(out)
print(d.pivot_table(index="config", columns="arm", values="auroc", sort=False).round(3).to_string())
