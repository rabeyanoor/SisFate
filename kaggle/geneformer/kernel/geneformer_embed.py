import glob
import sys
tok = sorted(glob.glob("/kaggle/input/**/tokens_V2-104M_CLcancer.npz", recursive=True))
print("token files:", tok, flush=True)
sys.argv = ["embed.py", "--tokens", tok[0], "--model", "V2-104M_CLcancer", "--out", "/kaggle/working/emb_V2-104M_CLcancer.npy", "--batch", "8"]
"""Geneformer cell embeddings from pre-computed rank-value tokens (standalone; runs on a Kaggle GPU).

Input: tokens_<model>.npz from scripts/21_geneformer.py tokens. Output: float16 array (cells x hidden),
the mean over gene positions (excluding <cls>/<eos>) of the penultimate hidden layer.
"""
import argparse
import time
from pathlib import Path

import numpy as np
import torch
from huggingface_hub import hf_hub_download
from transformers import BertForMaskedLM

SUBDIR = {"V1-10M": "Geneformer-V1-10M", "V2-104M_CLcancer": "Geneformer-V2-104M_CLcancer"}
ap = argparse.ArgumentParser()
ap.add_argument("--tokens", required=True)
ap.add_argument("--model", choices=list(SUBDIR), required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--batch", type=int, default=8)
args = ap.parse_args()

dev = "cuda" if torch.cuda.is_available() else "cpu"
for f in ["config.json", "model.safetensors"]:
    p = hf_hub_download("ctheodoris/Geneformer", f"{SUBDIR[args.model]}/{f}")
model = BertForMaskedLM.from_pretrained(Path(p).parent, output_hidden_states=True).eval().to(dev)
if dev == "cuda":
    model = model.half()
n_layers = model.config.num_hidden_layers
Z = np.load(args.tokens)
tokens, offsets, pad, special = Z["tokens"], Z["offsets"], int(Z["pad"]), bool(Z["special"])
lens = np.diff(offsets)
n = len(lens)
print(f"{args.model} on {dev}: {n} cells, median {int(np.median(lens))} tokens, {n_layers} layers", flush=True)

out = np.empty((n, model.config.hidden_size), np.float16)
order = np.argsort(lens)  # batch similar lengths to limit padding
t0 = time.time()
with torch.no_grad():
    for b in range(0, n, args.batch):
        ids = order[b: b + args.batch]
        L = int(lens[ids].max())
        x = torch.full((len(ids), L), pad, dtype=torch.long)
        m = torch.zeros((len(ids), L), dtype=torch.long)
        for r, i in enumerate(ids):
            x[r, : lens[i]] = torch.from_numpy(tokens[offsets[i]: offsets[i + 1]].astype(np.int64))
            m[r, : lens[i]] = 1
        h = model(input_ids=x.to(dev), attention_mask=m.to(dev)).hidden_states[n_layers - 1].float()
        if special:  # exclude <cls>/<eos> from the gene mean
            m[:, 0] = 0
            m[torch.arange(len(ids)), torch.from_numpy(lens[ids] - 1)] = 0
        mm = m.unsqueeze(-1).float().to(dev)
        out[ids] = ((h * mm).sum(1) / mm.sum(1)).cpu().numpy().astype(np.float16)
        if (b // args.batch) % 200 == 0:
            el = time.time() - t0
            print(f"{b + len(ids)}/{n} cells, {el:.0f}s, {(b + len(ids)) / el:.1f} cells/s", flush=True)
np.save(args.out, out)
print(f"done in {time.time() - t0:.0f}s -> {args.out}", flush=True)
