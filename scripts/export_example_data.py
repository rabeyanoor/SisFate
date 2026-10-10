"""Export a small, self-contained copy of the ReSisTrace data used by the main analysis.

data/example/resistrace_pca.npz holds, for the 32,642 labelled pre-treatment cells: the 50 principal components
(scripts/02_preprocess.py, cell cycle kept), the fate label, the lineage family, sample and arm of every cell, the
technical covariates, and the pre-treatment sister pairs. It is enough to rerun the main model, the fitness model
and the sister ceiling in seconds (notebooks/quickstart.ipynb) without downloading the raw data from GEO.

Source: Dai et al. (2024) Nat Commun 15:1158, GEO GSE223003.

Run: uv run python scripts/export_example_data.py   (needs data/processed/pre_keep.h5ad)
"""
import sys
from pathlib import Path

import anndata as ad
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from persist.labels import sister_pairs  # noqa: E402

a = ad.read_h5ad(ROOT / "data" / "processed" / "pre_keep.h5ad")
obs = a.obs
lab = obs["labeled"].to_numpy(bool)
pairs = sister_pairs(obs)                                     # positional indices into all pre-treatment cells
pairs = pairs[lab[pairs].all(1)]                              # keep pairs where both sisters are labelled
new_index = np.cumsum(lab) - 1                                # position among labelled cells
pairs = new_index[pairs]

o = obs[lab]
out = ROOT / "data" / "example" / "resistrace_pca.npz"
out.parent.mkdir(parents=True, exist_ok=True)
np.savez_compressed(
    out,
    X_pca=a.obsm["X_pca"][lab].astype(np.float32),
    y=o["y"].to_numpy(np.int8),
    family=np.asarray(o["lineage_group"].astype(str), dtype=str),
    sample=np.asarray(o["sample"].astype(str), dtype=str),
    arm=np.asarray(o["arm"].astype(str), dtype=str),
    cell_id=np.asarray(o.index, dtype=str),
    log_counts=np.log1p(o["nCount_RNA"].to_numpy(np.float32)),
    log_genes=np.log1p(o["nFeature_RNA"].to_numpy(np.float32)),
    pct_mt=o["percent.mt"].to_numpy(np.float32),
    s_score=o["S_score"].to_numpy(np.float32),
    g2m_score=o["G2M_score"].to_numpy(np.float32),
    sister_pairs=pairs.astype(np.int32),
)
print(f"{out}: {lab.sum()} cells, {len(pairs)} sister pairs, {out.stat().st_size / 1e6:.1f} MB")
