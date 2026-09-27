"""Read the GSE223003 per-sample TSVs into sparse AnnData objects.

GEO layout (verified): for each of 16 ReSisTrace samples there is
  GSM..._ReSisTrace_<Arm>_<rep>_<pre|post>_treatment_UMIcounts.tsv.gz   genes x cells, dense
  GSM..._ReSisTrace_<Arm>_<rep>_<pre|post>_treatment_cell_info.tsv.gz   Seurat meta.data
The dense matrices are ~30k x 5k, so they are streamed in row chunks to stay within a few GB of RAM.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import scipy.sparse as sp

SAMPLE_RE = re.compile(
    r"(?P<gsm>GSM\d+)_ReSisTrace_(?P<arm>[A-Za-z]+)_(?P<rep>\d)_(?P<timepoint>pre|post)_treatment_"
    r"(?P<kind>UMIcounts|cell_info)\.tsv\.gz$"
)


@dataclass(frozen=True)
class Sample:
    gsm: str
    arm: str
    replicate: int
    timepoint: str
    counts_path: Path
    info_path: Path

    @property
    def name(self) -> str:
        return f"{self.arm}_{self.replicate}_{self.timepoint}"


def discover_samples(raw_dir: Path) -> list[Sample]:
    found: dict[tuple, dict] = {}
    for f in sorted(Path(raw_dir).glob("*.tsv.gz")):
        m = SAMPLE_RE.search(f.name)
        if not m:
            continue
        key = (m["gsm"], m["arm"], int(m["rep"]), m["timepoint"])
        found.setdefault(key, {})[m["kind"]] = f
    samples = [
        Sample(gsm, arm, rep, tp, paths["UMIcounts"], paths["cell_info"])
        for (gsm, arm, rep, tp), paths in found.items()
        if {"UMIcounts", "cell_info"} <= paths.keys()
    ]
    if not samples:
        raise FileNotFoundError(f"No ReSisTrace TSVs in {raw_dir}; run scripts/00_download.sh first")
    return sorted(samples, key=lambda s: s.gsm)


def read_cell_info(path: Path) -> pd.DataFrame:
    info = pd.read_csv(path, sep="\t", index_col=0)
    info.index = info.index.astype(str)
    for col in info.columns:
        if info[col].dtype == object:
            info[col] = info[col].str.strip()
    return info


def read_counts_sparse(path: Path, chunk_genes: int = 2000) -> tuple[sp.csr_matrix, list[str], list[str]]:
    """Stream a genes x cells dense TSV into a cells x genes CSR matrix."""
    blocks, genes = [], []
    cells = None
    reader = pd.read_csv(path, sep="\t", index_col=0, chunksize=chunk_genes)
    for chunk in reader:
        if cells is None:
            cells = [str(c) for c in chunk.columns]
        genes.extend(str(g) for g in chunk.index)
        blocks.append(sp.csr_matrix(chunk.to_numpy(dtype=np.float32)))
    X = sp.vstack(blocks).T.tocsr()
    return X, cells, genes


def load_sample(sample: Sample, with_expression: bool = True) -> ad.AnnData:
    info = read_cell_info(sample.info_path)
    if with_expression:
        X, cells, genes = read_counts_sparse(sample.counts_path)
        missing = set(cells) ^ set(info.index)
        if missing:
            raise ValueError(f"{sample.name}: {len(missing)} cells differ between counts and cell_info")
        info = info.loc[cells]
    else:
        X, genes = sp.csr_matrix((len(info), 0), dtype=np.float32), []
    obs = info.copy()
    obs["sample"] = sample.name
    obs["gsm"] = sample.gsm
    obs["arm"] = sample.arm
    obs["replicate"] = sample.replicate
    obs["timepoint"] = sample.timepoint
    # Cell barcodes repeat across samples; prefix with the sample name.
    obs.index = [f"{sample.name}:{c}" for c in obs.index]
    var = pd.DataFrame(index=pd.Index(genes, name="gene_id_versioned"))
    var["ensembl"] = [g.split(".")[0] for g in genes]
    adata = ad.AnnData(X=X, obs=obs, var=var)
    adata.var_names = adata.var["ensembl"].values
    adata.var_names_make_unique()
    return adata


def align_genes(adata: ad.AnnData, genes: pd.Index) -> ad.AnnData:
    """Reindex columns to `genes`; genes the authors filtered out of this sample become zero counts."""
    pos = genes.get_indexer(adata.var_names)
    if (pos < 0).any():
        raise ValueError("sample has genes outside the target gene set")
    X = adata.X.tocsc() if sp.issparse(adata.X) else sp.csc_matrix(adata.X)
    M = sp.csr_matrix((np.ones(len(pos), np.float32), (np.arange(len(pos)), pos)), shape=(len(pos), len(genes)))
    out = ad.AnnData(X=(X @ M).tocsr().astype(np.float32), obs=adata.obs.copy(),
                     var=pd.DataFrame({"ensembl": genes}, index=genes))
    return out
