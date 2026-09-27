"""PERSIST-GNN and its ablations (same splits and shuffled controls as the baselines).

  mlp                     encoder only (no graph, no pretraining)
  mlp_pretrain            + sister-pair contrastive pretraining
  persist_gnn_nopretrain  + kNN graph message passing
  persist_gnn             graph + pretraining (full model)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.runner import cli  # noqa: E402
from persist.utils import load_config  # noqa: E402

cli("gnn", ["mlp", "mlp_pretrain", "persist_gnn_nopretrain", "persist_gnn"], load_config()["gnn"]["seeds"])
