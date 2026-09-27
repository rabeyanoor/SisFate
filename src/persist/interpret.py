"""Genes behind the pre-resistant state: replicate-consistent DE, drug-vs-fitness contrast, model weights."""
from __future__ import annotations

import numpy as np
import pandas as pd
import scanpy as sc
from scipy import stats

from .models.baselines import logistic


def de_sample(adata, sample: str) -> pd.DataFrame:
    """Wilcoxon pre-resistant vs pre-sensitive inside one sample (log-normalised X)."""
    sub = adata[(adata.obs["sample"] == sample).to_numpy() & adata.obs["labeled"].to_numpy()].copy()
    sub.obs["grp"] = np.where(sub.obs["y"] == 1, "pos", "neg")
    sc.tl.rank_genes_groups(sub, "grp", groups=["pos"], reference="neg", method="wilcoxon", pts=False)
    r = sc.get.rank_genes_groups_df(sub, group="pos").set_index("names")
    return r.rename(columns={"scores": "z", "logfoldchanges": "logfc", "pvals_adj": "padj"})[["z", "logfc", "padj"]]


def de_arm(adata, arm: str) -> pd.DataFrame:
    """Combine replicates with Stouffer's z; flag sign-consistent genes."""
    samples = sorted(adata.obs.loc[adata.obs["arm"] == arm, "sample"].unique())
    per = {s: de_sample(adata, s) for s in samples}
    genes = sorted(set.intersection(*(set(d.index) for d in per.values())))
    Z = pd.DataFrame({s: per[s].loc[genes, "z"] for s in samples})
    L = pd.DataFrame({s: per[s].loc[genes, "logfc"] for s in samples})
    out = pd.DataFrame(index=genes)
    out["z"] = Z.sum(1) / np.sqrt(Z.shape[1])
    out["logfc"] = L.mean(1)
    out["consistent"] = (np.sign(Z).nunique(axis=1) == 1)
    out["p"] = 2 * stats.norm.sf(out["z"].abs())
    out["padj"] = stats.false_discovery_control(out["p"])
    for s in samples:
        out[f"z_{s}"] = Z[s]
    out["symbol"] = adata.var.loc[genes, "symbol"].values
    return out.sort_values("z", ascending=False)


def drug_specific(de_drug: pd.DataFrame, de_ctrl: pd.DataFrame, fdr: float) -> pd.DataFrame:
    """Genes DE in the drug arm beyond what the control (fitness) arm shows.

    z_diff = (z_drug - z_ctrl) / sqrt(2) is a simple two-sample contrast of independent z-scores.
    """
    g = de_drug.index.intersection(de_ctrl.index)
    out = pd.DataFrame({
        "symbol": de_drug.loc[g, "symbol"], "z_drug": de_drug.loc[g, "z"], "z_ctrl": de_ctrl.loc[g, "z"],
        "padj_drug": de_drug.loc[g, "padj"], "consistent": de_drug.loc[g, "consistent"],
    })
    out["z_diff"] = (out["z_drug"] - out["z_ctrl"]) / np.sqrt(2)
    out["padj_diff"] = stats.false_discovery_control(2 * stats.norm.sf(out["z_diff"].abs()))
    out["class"] = np.select(
        [(out["padj_drug"] < fdr) & (out["padj_diff"] < fdr) & out["consistent"],
         (out["padj_drug"] < fdr) & out["consistent"]],
        ["drug_specific", "shared_with_fitness"], "ns")
    return out.sort_values("z_diff", ascending=False)


def model_gene_weights(ctx, arm: str, seed: int = 0) -> pd.DataFrame:
    """Standardised logistic coefficients on HVG features, trained on all labelled cells of an arm."""
    m = ctx.obs["labeled"].to_numpy() & (ctx.obs["arm"] == arm).to_numpy()
    X = ctx.features("hvg")
    _, model = logistic(X[m], ctx.y[m], X[m][:1], ctx.cfg["baselines"]["logistic_C"], seed)
    hvg = ctx.adata.var_names[ctx.adata.var["highly_variable"]]
    coef = model[-1].coef_.ravel()
    return pd.DataFrame({"symbol": ctx.adata.var.loc[hvg, "symbol"].values, "coef": coef},
                        index=hvg).sort_values("coef", ascending=False)


# mitochondrial / ribosomal transcripts track depth and stress (QC axes) and do not transfer to bulk data
TECHNICAL = r"^(MT-|MTATP|MTND|MTCO|MTCY|RP[SL]\d)"


def signature(table: pd.DataFrame, n: int, z_col: str, fdr_col: str, fdr: float, cls: str | None = None) -> dict:
    t = table if cls is None else table[table["class"] == cls]
    t = t[(t[fdr_col] < fdr) & ~t["symbol"].str.match(TECHNICAL)]
    return {"up": t[t[z_col] > 0].nlargest(n, z_col)["symbol"].tolist(),
            "down": t[t[z_col] < 0].nsmallest(n, z_col)["symbol"].tolist()}


def hallmark_gsea(table: pd.DataFrame, z_col: str, ref_dir, seed: int = 0, permutations: int = 1000) -> pd.DataFrame:
    """Preranked GSEA of a z-score column against MSigDB Hallmark (Enrichr copy, cached on disk)."""
    import json
    from pathlib import Path

    import gseapy as gp

    cache = Path(ref_dir) / "MSigDB_Hallmark_2020.json"
    if cache.exists():
        gene_sets = json.loads(cache.read_text())
    else:
        gene_sets = gp.get_library("MSigDB_Hallmark_2020", organism="Human")
        cache.write_text(json.dumps(gene_sets))
    rnk = table[["symbol", z_col]].dropna()
    rnk = rnk[~rnk["symbol"].str.match(TECHNICAL)].drop_duplicates("symbol").set_index("symbol")[z_col]
    res = gp.prerank(rnk=rnk.sort_values(ascending=False), gene_sets=gene_sets, permutation_num=permutations,
                     min_size=10, max_size=500, seed=seed, threads=4, outdir=None, verbose=False).res2d
    return res[["Term", "NES", "NOM p-val", "FDR q-val", "Lead_genes"]].sort_values("NES", ascending=False)
