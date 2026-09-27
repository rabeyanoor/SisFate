"""Cell-cell kNN similarity graph (built on label-free PCA features)."""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from sklearn.neighbors import NearestNeighbors


def knn_graph(X: np.ndarray, samples: np.ndarray, k: int = 15, metric: str = "cosine",
              within_sample: bool = True) -> sp.csr_matrix:
    """Symmetric, row-normalised kNN adjacency without self loops (mean aggregation operator)."""
    n = len(X)
    rows, cols = [], []
    blocks = [np.flatnonzero(samples == s) for s in np.unique(samples)] if within_sample else [np.arange(n)]
    for idx in blocks:
        kk = min(k + 1, len(idx))
        nn = NearestNeighbors(n_neighbors=kk, metric=metric).fit(X[idx])
        _, nbr = nn.kneighbors(X[idx])
        rows.append(np.repeat(idx, kk - 1))
        cols.append(idx[nbr[:, 1:]].ravel())
    rows, cols = np.concatenate(rows), np.concatenate(cols)
    A = sp.coo_matrix((np.ones(len(rows), np.float32), (rows, cols)), shape=(n, n)).tocsr()
    A = ((A + A.T) > 0).astype(np.float32)
    deg = np.asarray(A.sum(1)).ravel()
    deg[deg == 0] = 1.0
    return sp.diags(1.0 / deg) @ A


def smooth(X: np.ndarray, A: sp.csr_matrix, alpha: float) -> np.ndarray:
    """Non-learned graph baseline: blend each cell with its neighbourhood mean."""
    return ((1 - alpha) * X + alpha * (A @ X)).astype(np.float32)
