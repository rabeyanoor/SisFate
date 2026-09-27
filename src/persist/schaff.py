"""Loading and lineage assignment for the multi-treatment clonal-tracing data of Schaff et al. (2026).

Design (GEO GSE279162): WM989 BRAF-mutant melanoma cells carrying transcribed Rewind barcodes were expanded,
a sample of the untreated population was profiled by scRNA-seq ("naive", three lanes), and the rest was split
across six treatments (dabrafenib, trametinib, CoCl2, acidic medium, cisplatin, doxorubicin). After four weeks
the surviving cells were profiled with paired barcode sequencing. Lineage barcodes are stored in the same
matrices as the genes, as features of type "Custom".

So an untreated cell can be labelled six times over: for each treatment, did any cell of its lineage survive?
Unlike ReSisTrace there is no drug-free arm carried through the four weeks, so there is no fitness model.
Pre-treatment clone size stands in for it: it measures how well a lineage grows in culture before any drug,
and the authors themselves report that it correlates with post-treatment abundance for four of the six
treatments.

Barcode assignment. The authors assign lineages with a Bayesian posterior after merging correlated barcodes.
We use a simpler and more transparent rule, and report how results move with its thresholds: near-duplicate
barcodes (Pearson r >= `merge_r` over cells, which arise from sequencing errors) are merged, and a cell is
assigned the barcode holding at least `min_umi` UMIs and more than `min_frac` of its barcode UMIs; otherwise
it is unassigned, so a cell split evenly between two barcodes is dropped rather than guessed. Clone counts therefore differ from the published ones.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

SAMPLES = {
    "Naive1": "GSM8562999", "Naive2": "GSM8563000", "Naive3": "GSM8563001",
    "Dabrafenib": "GSM8563002", "Trametinib": "GSM8563003", "CoCl2": "GSM8563004",
    "Acid": "GSM8563005", "Cisplatin": "GSM8563006", "Doxorubicin": "GSM8563007",
}
NAIVE = ["Naive1", "Naive2", "Naive3"]
TREATMENTS = ["Dabrafenib", "Trametinib", "CoCl2", "Acid", "Cisplatin", "Doxorubicin"]


def _read_mtx(raw: Path, sample: str):
    """Returns (counts cells x features CSR, features DataFrame, cell ids)."""
    gsm = SAMPLES[sample]
    stem = f"{gsm}_{sample}"
    feat = pd.read_csv(raw / f"{stem}_filtered_features.tsv.gz", sep="\t", header=None,
                       names=["id", "symbol", "type"])
    cells = pd.read_csv(raw / f"{stem}_filtered_barcodes.tsv.gz", sep="\t", header=None)[0].to_numpy()
    from scipy.io import mmread
    X = sp.csr_matrix(mmread(raw / f"{stem}_filtered_matrix.mtx.gz")).T.tocsr()  # features x cells -> cells x features
    if X.shape != (len(cells), len(feat)):
        raise ValueError(f"{sample}: matrix {X.shape} does not match {len(cells)} cells x {len(feat)} features")
    return X, feat, np.array([f"{sample}:{c}" for c in cells])


def load_sample(raw: Path, sample: str):
    """Split a sample into its gene matrix and its lineage-barcode matrix."""
    X, feat, cells = _read_mtx(Path(raw), sample)
    is_gene = (feat["type"] == "Gene Expression").to_numpy()
    return X[:, is_gene], feat.loc[is_gene, "symbol"].to_numpy(), X[:, ~is_gene], feat.loc[~is_gene, "id"].to_numpy(), cells


def merge_similar_barcodes(L: sp.csr_matrix, names: np.ndarray, merge_r: float = 0.55, min_total: int = 5):
    """Merge barcodes whose per-cell count vectors are near-parallel (sequencing errors split one clone).

    Similarity is cosine over cells, computed with a sparse product so that only barcodes sharing at least one
    cell are ever compared; a dense correlation matrix over 10^5 barcodes would not fit in memory. For sparse
    non-negative count vectors cosine and Pearson correlation are close, but this is not identical to the
    authors' merging step. Connected components above `merge_r` are summed.
    """
    tot = np.asarray(L.sum(0)).ravel()
    keep = np.flatnonzero(tot >= min_total)
    if len(keep) < 2:
        return L, names
    A = L[:, keep].tocsc().astype(np.float64)
    norm = np.sqrt(np.asarray(A.multiply(A).sum(0)).ravel())
    norm[norm == 0] = 1
    A = A @ sp.diags(1 / norm)
    S = (A.T @ A).tocoo()
    m = (S.data >= merge_r) & (S.row != S.col)
    G = sp.csr_matrix((np.ones(m.sum()), (S.row[m], S.col[m])), shape=(len(keep), len(keep)))
    from scipy.sparse.csgraph import connected_components
    n_comp, comp = connected_components(G, directed=False)
    order = np.argsort(comp, kind="stable")
    bounds = np.cumsum(np.bincount(comp))[:-1]
    out = sp.csr_matrix((L.shape[0], n_comp))
    cols, reps = [], []
    for grp in np.split(order, bounds):
        idx = keep[grp]
        cols.append(sp.csr_matrix(L[:, idx].sum(1)))
        reps.append(names[idx][np.argmax(tot[idx])])
    out = sp.hstack(cols).tocsr()
    return out, np.array(reps)


def assign_lineage(L: sp.csr_matrix, names: np.ndarray, min_umi: int = 2, min_frac: float = 0.5) -> np.ndarray:
    """One lineage per cell: the dominant barcode, if it is dominant enough. Otherwise None."""
    L = L.tocsr()
    out = np.full(L.shape[0], None, dtype=object)
    tot = np.asarray(L.sum(1)).ravel()
    for i in range(L.shape[0]):
        lo, hi = L.indptr[i], L.indptr[i + 1]
        if hi == lo or tot[i] == 0:
            continue
        vals, cols = L.data[lo:hi], L.indices[lo:hi]
        k = np.argmax(vals)
        if vals[k] >= min_umi and vals[k] / tot[i] > min_frac:  # strict: an exact tie stays unassigned
            out[i] = names[cols[k]]
    return out


def build(raw: Path, merge_r: float = 0.55, min_umi: int = 2, min_frac: float = 0.5, log=None):
    """Assign lineages in every sample on a common barcode space, and label the untreated cells.

    Returns (counts of untreated cells x genes, gene names, obs) where obs has one column per treatment:
    `y_<treatment>` is 1 when the cell's lineage is seen among that treatment's survivors.
    """
    raw = Path(raw)
    genes_ref = None
    lin_parts, gene_parts, cell_parts, sample_parts = [], [], [], []
    for s in SAMPLES:
        G, genes, L, lin_names, cells = load_sample(raw, s)
        if genes_ref is None:
            genes_ref, lin_ref = genes, lin_names
        elif not (np.array_equal(genes, genes_ref) and np.array_equal(lin_names, lin_ref)):
            raise ValueError(f"{s}: feature order differs from the first sample")
        gene_parts.append(G)
        lin_parts.append(L)
        cell_parts.append(cells)
        sample_parts.append(np.repeat(s, len(cells)))
        if log:
            log.info(f"{s}: {G.shape[0]} cells, {int(L.sum())} lineage UMIs")

    L_all = sp.vstack(lin_parts).tocsr()
    L_all, lin_ref = merge_similar_barcodes(L_all, lin_ref, merge_r)
    lineage = assign_lineage(L_all, lin_ref, min_umi, min_frac)
    sample = np.concatenate(sample_parts)
    cells = np.concatenate(cell_parts)
    if log:
        log.info(f"{np.sum(lineage != None)} of {len(lineage)} cells assigned a lineage "  # noqa: E711
                 f"({len(set(lineage[lineage != None]))} lineages after merging)")  # noqa: E711

    G_all = sp.vstack(gene_parts).tocsr()  # same row order as sample / cells / lineage
    naive = np.isin(sample, NAIVE) & (lineage != None)  # noqa: E711
    obs = pd.DataFrame({"cell": cells[naive], "sample": sample[naive], "lineage": lineage[naive]}).set_index("cell")
    obs["clone_size"] = obs.groupby("lineage")["lineage"].transform("size")
    for t in TREATMENTS:
        survivors = set(lineage[(sample == t) & (lineage != None)])  # noqa: E711
        obs[f"y_{t}"] = obs["lineage"].isin(survivors).astype(int)
    return G_all[naive], genes_ref, obs
