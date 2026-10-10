# GPU step: Geneformer and scGPT embeddings

Only the forward passes of the two foundation models need a GPU; everything else runs on a CPU. They were run on
a free Kaggle notebook with one NVIDIA T4 GPU, but any machine with a CUDA GPU works.

| Model | 1. Prepare input (CPU) | 2. Embed (GPU) | 3. Analyse (CPU) |
|---|---|---|---|
| Geneformer V2-104M_CLcancer | `python scripts/21_geneformer.py tokens` writes `tokens_V2-104M_CLcancer.npz` | `geneformer/kernel/geneformer_embed.py` (calls `geneformer/embed.py`), about 1 h on a T4 | put `emb_V2-104M_CLcancer.npy` in `data/processed/geneformer/`, then `python scripts/21_geneformer.py analyze` |
| scGPT whole-human | `python scripts/29_scgpt.py export` writes `counts.npz` | `scgpt/kernel/scgpt_embed.py`, about 7 min on a T4 | put `emb_scgpt_human.npy` in `data/processed/scgpt/`, then `python scripts/29_scgpt.py analyze` |

On Kaggle: upload the input file of step 1 as a private dataset, create a notebook with the GPU accelerator and
internet access, attach the dataset, and run the script of step 2. The scripts find their input under
`/kaggle/input/` and write the embedding to `/kaggle/working/`. Elsewhere, edit those two paths.
