"""PERSIST-GNN: encoder -> GraphSAGE-style mean-aggregation layers -> logit.

n_layers = 0 gives the matched MLP ablation (identical training, no neighbourhood information).
Training is full-batch over all pre-treatment cells; the loss only sees training labels, and test
cells contribute features (never labels) through message passing.
"""
from __future__ import annotations

import copy

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import average_precision_score


class Encoder(nn.Module):
    def __init__(self, d_in: int, hidden: int, d_out: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden, d_out),
        )

    def forward(self, x):
        return self.net(x)


class SAGELayer(nn.Module):
    def __init__(self, d: int, dropout: float):
        super().__init__()
        self.self_lin = nn.Linear(d, d)
        self.neigh_lin = nn.Linear(d, d, bias=False)
        self.norm = nn.LayerNorm(d)
        self.dropout = dropout

    def forward(self, h, A):
        out = self.self_lin(h) + self.neigh_lin(A @ h)
        out = F.dropout(F.gelu(self.norm(out)), self.dropout, self.training)
        return h + out  # residual keeps the cell's own state dominant


class PersistGNN(nn.Module):
    def __init__(self, d_in: int, hidden: int, emb_dim: int, n_layers: int, dropout: float):
        super().__init__()
        self.encoder = Encoder(d_in, hidden, emb_dim, dropout)
        self.layers = nn.ModuleList([SAGELayer(emb_dim, dropout) for _ in range(n_layers)])
        self.head = nn.Linear(emb_dim, 1)

    def embed(self, x, A=None):
        h = self.encoder(x)
        for layer in self.layers:
            h = layer(h, A)
        return h

    def forward(self, x, A=None):
        return self.head(self.embed(x, A)).squeeze(-1)


def to_torch_sparse(A: sp.spmatrix) -> torch.Tensor:
    A = A.tocoo()
    idx = torch.from_numpy(np.vstack([A.row, A.col]).astype(np.int64))
    coo = torch.sparse_coo_tensor(idx, torch.from_numpy(A.data.astype(np.float32)), A.shape,
                                  check_invariants=True).coalesce()
    return coo.to_sparse_csr()  # CSR spmm is markedly faster on CPU


def train_gnn(X: torch.Tensor, A: torch.Tensor | None, y: np.ndarray, tr_idx: np.ndarray, va_idx: np.ndarray,
              cfg: dict, seed: int, n_layers: int, encoder_state: dict | None = None) -> PersistGNN:
    g = cfg["gnn"]
    torch.manual_seed(seed)
    model = PersistGNN(X.shape[1], g["hidden"], g["emb_dim"], n_layers, g["dropout"])
    params = [{"params": [p for n, p in model.named_parameters() if not n.startswith("encoder.")], "lr": g["lr"]}]
    enc_lr = g["lr"]
    if encoder_state is not None:
        model.encoder.load_state_dict(encoder_state)
        enc_lr = g["lr"] * cfg["contrastive"]["finetune_lr_mult"]
    params.append({"params": model.encoder.parameters(), "lr": enc_lr})
    opt = torch.optim.AdamW(params, weight_decay=g["weight_decay"])

    y_t = torch.from_numpy(y.astype(np.float32))
    tr_t, va_t = torch.from_numpy(tr_idx), torch.from_numpy(va_idx)
    pos = y[tr_idx].sum()
    pos_weight = torch.tensor((len(tr_idx) - pos) / max(pos, 1), dtype=torch.float32)

    best, best_state, bad = -np.inf, None, 0
    for _ in range(g["max_epochs"]):
        model.train()
        opt.zero_grad()
        logits = model(X, A)
        loss = F.binary_cross_entropy_with_logits(logits[tr_t], y_t[tr_t], pos_weight=pos_weight)
        loss.backward()
        opt.step()

        model.eval()
        with torch.no_grad():
            va_score = model(X, A)[va_t].numpy()
        ap = average_precision_score(y[va_idx], va_score) if 0 < y[va_idx].sum() < len(va_idx) else -loss.item()
        if ap > best + 1e-4:
            best, best_state, bad = ap, copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
            if bad >= g["patience"]:
                break
    model.load_state_dict(best_state)
    model.eval()
    return model


@torch.no_grad()
def predict(model: PersistGNN, X: torch.Tensor, A: torch.Tensor | None, idx: np.ndarray) -> np.ndarray:
    model.eval()
    return torch.sigmoid(model(X, A)[torch.from_numpy(idx)]).numpy()
