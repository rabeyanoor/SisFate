"""Synthetic checks for the lineage assignment used on Schaff et al. (2026): error-split barcodes merge,
cells get the right clone, and ambiguous cells are dropped rather than guessed."""
import numpy as np, scipy.sparse as sp
from persist.schaff import merge_similar_barcodes, assign_lineage

def test_merge_assign():
  # two barcodes that are really one clone (same cells, error-split) + one independent barcode
  rng = np.random.default_rng(0)
  n=200
  true = rng.integers(0,2,n)           # clone A cells
  c1 = (true*rng.integers(3,10,n))     # barcode A
  c1b = (true*rng.integers(1,4,n))     # error variant of A -> same cells
  c2 = ((1-true)*rng.integers(3,10,n)) # barcode B
  L = sp.csr_matrix(np.column_stack([c1,c1b,c2]).astype(float))
  names = np.array(["A","Aerr","B"])
  M, rep = merge_similar_barcodes(L, names, merge_r=0.55, min_total=5)
  print("merged shape", M.shape, "reps", sorted(rep))
  assert M.shape[1]==2, "A and its error variant should merge"
  lin = assign_lineage(M, rep, min_umi=2, min_frac=0.5)
  got = np.array([x is not None for x in lin])
  print("assigned", got.sum(), "of", n)
  # every cell should get the clone matching its true label
  lab = np.array([str(x) for x in lin])
  a_name = rep[[i for i,r in enumerate(rep) if r in ("A","Aerr")][0]]
  agree = np.mean((lab==a_name)==(true==1))
  print("agreement with truth", round(agree,3))
  assert agree > 0.95
  # a cell with two equal barcodes must be left unassigned
  amb = sp.csr_matrix(np.array([[5.0,0,5.0]]))
  assert assign_lineage(amb, names, 2, 0.5)[0] is None
  print("PASS")
