"""Single-cell foundation-model features: does a pretrained transformer (Geneformer) recover more
signal than 50 principal components?

Cells are rank-value encoded as in Geneformer (counts scaled to 10,000 per cell, divided by each gene's
corpus median, genes ranked, top `input_size` kept; V2 adds <cls>/<eos>). The cell embedding is the mean of
gene embeddings from the penultimate layer (Geneformer's default). Embeddings are z-scored within each sample
(as the PCA input is) and then used exactly like the principal components: within-arm grouped CV and the
fitness analysis.

Three steps, so the transformer can run on a GPU elsewhere (we used a Kaggle T4; see kaggle/geneformer/):
  tokens   write the rank-value encodings  -> data/processed/geneformer/tokens_<model>.npz   (CPU, minutes)
  embed    run the model                    -> data/processed/geneformer/emb_<model>.npy      (GPU; kaggle/geneformer/embed.py)
  analyze  fitness analysis on embeddings   -> results/sensitivity_representations.csv (appended)

Run: uv run --with transformers --with huggingface_hub python scripts/21_geneformer.py tokens --model V2-104M_CLcancer
"""
import argparse
import pickle
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.fitness import fitness_analysis  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

REPO = "ctheodoris/Geneformer"
MODELS = {  # subdir, token dict, median dict, input size, uses <cls>/<eos>
    "V1-10M": ("Geneformer-V1-10M", "geneformer/gene_dictionaries_30m/token_dictionary_gc30M.pkl",
               "geneformer/gene_dictionaries_30m/gene_median_dictionary_gc30M.pkl", 2048, False),
    "V2-104M_CLcancer": ("Geneformer-V2-104M_CLcancer", "geneformer/token_dictionary_gc104M.pkl",
                         "geneformer/gene_median_dictionary_gc104M.pkl", 4096, True),
}

ap = argparse.ArgumentParser()
ap.add_argument("step", choices=["tokens", "embed", "analyze"])
ap.add_argument("--config")
ap.add_argument("--model", choices=list(MODELS), default="V2-104M_CLcancer")
ap.add_argument("--batch", type=int, default=8)
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("geneformer")
subdir, tok_f, med_f, input_size, special = MODELS[args.model]
out_dir = Path(cfg["paths"]["processed_dir"]) / "geneformer"
out_dir.mkdir(exist_ok=True)
tok_path, emb_path = out_dir / f"tokens_{args.model}.npz", out_dir / f"emb_{args.model}.npy"

if args.step == "tokens":
    from huggingface_hub import hf_hub_download

    tok = pickle.load(open(hf_hub_download(REPO, tok_f), "rb"))
    med = pickle.load(open(hf_hub_download(REPO, med_f), "rb"))
    obs = ad.read_h5ad(Path(cfg["paths"]["processed_dir"]) / "pre_keep.h5ad", backed="r").obs
    seqs, cells = [], []
    for s in obs["sample"].unique():
        a = ad.read_h5ad(Path(cfg["paths"]["processed_dir"]) / "samples" / f"{s}.h5ad")
        a = a[obs.index[obs["sample"] == s]]
        genes = a.var_names  # Ensembl IDs are required; fall back to the gene_ids column if present
        if not genes.str.startswith("ENSG").any() and "gene_ids" in a.var:
            genes = pd.Index(a.var["gene_ids"])
        keep = np.array([g in tok and g in med for g in genes])
        g_tok = np.array([tok[g] for g in genes[keep]])
        g_med = np.array([med[g] for g in genes[keep]], dtype=np.float64)
        counts = sp.csr_matrix(a.X)
        tot = np.asarray(counts.sum(1)).ravel()
        X = counts[:, np.flatnonzero(keep)].tocsr().astype(np.float64)
        for i in range(X.shape[0]):
            lo, hi = X.indptr[i], X.indptr[i + 1]
            cols, vals = X.indices[lo:hi], X.data[lo:hi]
            v = vals / tot[i] * 1e4 / g_med[cols]
            t = g_tok[cols[np.argsort(-v, kind="stable")[: input_size - (2 if special else 0)]]]
            if special:
                t = np.concatenate([[tok["<cls>"]], t, [tok["<eos>"]]])
            seqs.append(t.astype(np.int32))
        cells += list(a.obs_names)
        log.info(f"{s}: {a.n_obs} cells, {keep.sum()} genes in vocabulary, median {int(np.median([len(q) for q in seqs[-a.n_obs:]]))} tokens")
    lens = np.array([len(q) for q in seqs])
    np.savez_compressed(tok_path, tokens=np.concatenate(seqs), offsets=np.concatenate([[0], np.cumsum(lens)]),
                        cells=np.array(cells), pad=np.int32(tok.get("<pad>", 0)), special=special)
    log.info(f"wrote {tok_path} ({len(cells)} cells)")

elif args.step == "embed":  # CPU fallback; the GPU run uses the identical kaggle/geneformer/embed.py
    import subprocess
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "kaggle" / "geneformer" / "embed.py"),
                    "--tokens", str(tok_path), "--model", args.model, "--out", str(emb_path), "--batch", str(args.batch)],
                   check=True)

else:
    ctx = load_context(cfg, "keep")
    cells = np.load(tok_path)["cells"]
    E = pd.DataFrame(np.load(emb_path).astype(np.float64), index=cells).loc[ctx.obs.index].to_numpy()
    for s in np.unique(ctx.samples):  # z-score within sample, as for the PCA input
        m = ctx.samples == s
        E[m] = (E[m] - E[m].mean(0)) / (E[m].std(0) + 1e-8)
    ctx.feats["pca"] = E
    rows = []
    for arm in [a for a in cfg["data"]["arms"] if a != "Control"]:
        r = fitness_analysis(ctx, arm, "Control", "pca", cfg["seed"])
        r.update(representation=f"geneformer_{args.model}", n_dims=E.shape[1], config_hash=cfg["_hash"])
        rows.append(r)
        log.info(f"{args.model} {arm}: drug={r['auroc_drug_model_on_drug']:.3f} fitness={r['auroc_fitness_model_on_drug']:.3f} "
                 f"control={r['auroc_control_model_on_control']:.3f} spec_matched={r['specificity_index_size_matched']:.3f}")
    res = Path(cfg["paths"]["results_dir"]) / "sensitivity_representations.csv"
    old = pd.read_csv(res)
    old = old[old["representation"] != f"geneformer_{args.model}"]
    pd.concat([old, pd.DataFrame(rows)], ignore_index=True).to_csv(res, index=False)
    print(pd.DataFrame(rows)[["drug_arm", "auroc_drug_model_on_drug", "auroc_fitness_model_on_drug",
                              "auroc_control_model_on_control", "specificity_index_size_matched"]].round(3).to_string(index=False))
