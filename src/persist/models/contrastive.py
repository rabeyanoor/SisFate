"""Sister-pair contrastive pretraining of the cell encoder (label-free).

Pre-treatment sisters share a lineage but were never treated, so pulling them together in
embedding space learns the *heritable* part of transcriptional state -- the same quantity that
bounds predictability in the ceiling analysis (ceiling.py). An augmentation-only NT-Xent term on
unpaired cells regularises the encoder so it does not collapse onto the few thousand pairs.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F

from .gnn import Encoder


def nt_xent(z1: torch.Tensor, z2: torch.Tensor, temperature: float) -> torch.Tensor:
    z = F.normalize(torch.cat([z1, z2]), dim=1)
    sim = z @ z.T / temperature
    n = len(z1)
    sim.fill_diagonal_(-1e9)
    target = torch.cat([torch.arange(n, 2 * n), torch.arange(0, n)])
    return F.cross_entropy(sim, target)


def augment(x: torch.Tensor, noise: float, drop: float) -> torch.Tensor:
    mask = (torch.rand_like(x) > drop).float()
    return (x + noise * torch.randn_like(x)) * mask


def pretrain_encoder(X: torch.Tensor, pairs: np.ndarray, pool_idx: np.ndarray, cfg: dict, seed: int) -> dict:
    """pairs: (n,2) sister indices allowed for pretraining; pool_idx: cells allowed for the SimCLR term."""
    c, g = cfg["contrastive"], cfg["gnn"]
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    enc = Encoder(X.shape[1], g["hidden"], g["emb_dim"], g["dropout"])
    opt = torch.optim.AdamW(enc.parameters(), lr=c["lr"], weight_decay=g["weight_decay"])
    bs = min(c["batch_pairs"], len(pairs))
    steps_per_epoch = max(1, len(pairs) // bs)
    for _ in range(c["epochs"]):
        order = rng.permutation(len(pairs))
        for step in range(steps_per_epoch):
            b = pairs[order[step * bs:(step + 1) * bs]]
            # random orientation so the encoder is symmetric in (a, b)
            flip = rng.random(len(b)) < 0.5
            b = np.where(flip[:, None], b[:, ::-1], b)
            xa = augment(X[b[:, 0]], c["aug_noise"], c["aug_dropout"])
            xb = augment(X[b[:, 1]], c["aug_noise"], c["aug_dropout"])
            loss = nt_xent(enc(xa), enc(xb), c["temperature"])
            if c["simclr_weight"] > 0:
                u = X[rng.choice(pool_idx, size=bs, replace=False)]
                loss = loss + c["simclr_weight"] * nt_xent(
                    enc(augment(u, c["aug_noise"], c["aug_dropout"])),
                    enc(augment(u, c["aug_noise"], c["aug_dropout"])), c["temperature"])
            opt.zero_grad()
            loss.backward()
            opt.step()
    enc.eval()
    return {k: v.detach().clone() for k, v in enc.state_dict().items()}
