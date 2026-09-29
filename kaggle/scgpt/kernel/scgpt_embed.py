"""scGPT whole-human cell embeddings for the ReSisTrace pre-treatment cells (runs on a Kaggle GPU).

Reproduces scgpt.tasks.cell_emb.embed_data (scGPT 0.2.4) without importing the scgpt package root, which pulls
in torchtext, a library that no longer builds against current PyTorch. The model, its two helper modules and the
data collator are copied verbatim from the installed wheel into a local package; the two binning functions the
collator needs are extracted verbatim from scgpt/preprocess.py. Everything else follows embed_data: genes not in
the scGPT vocabulary are dropped, a <cls> token is prepended, expression is binned into 51 per-cell bins, at most
1,200 tokens are kept (random sampling beyond that, as in scGPT), and the <cls> output is L2-normalised.

Input : counts.npz from scripts/29_scgpt.py export (raw counts, cells x genes, gene symbols)
Output: emb_scgpt_human.npy (cells x 512, same cell order as counts.npz)
"""
import ast
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "scgpt==0.2.4", "--no-deps"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gdown"], check=True)

import numpy as np  # noqa: E402
import scipy.sparse as sp  # noqa: E402
import torch  # noqa: E402

SEED = 0
np.random.seed(SEED)
torch.manual_seed(SEED)
WORK = Path("/kaggle/working")
IN = Path(glob.glob("/kaggle/input/**/counts.npz", recursive=True)[0])

# ---- 1. a minimal local copy of the scGPT modules needed for inference
import importlib.util  # noqa: E402
src = Path(importlib.util.find_spec("scgpt").submodule_search_locations[0])
pkg = WORK / "scgptmini"
(pkg / "model").mkdir(parents=True, exist_ok=True)
for f in ["model.py", "dsbn.py", "grad_reverse.py"]:
    shutil.copy(src / "model" / f, pkg / "model" / f)
(pkg / "model" / "__init__.py").write_text("")
shutil.copy(src / "data_collator.py", pkg / "data_collator.py")
tree = ast.parse((src / "preprocess.py").read_text())
funcs = [ast.get_source_segment((src / "preprocess.py").read_text(), n) for n in tree.body
         if isinstance(n, ast.FunctionDef) and n.name in ("_digitize", "binning")]
(pkg / "preprocess.py").write_text("import logging\nfrom typing import Union\nimport numpy as np\nimport torch\n"
                                   "logger = logging.getLogger('scgptmini')\n\n" + "\n\n".join(funcs) + "\n")
(pkg / "__init__.py").write_text("")
sys.path.insert(0, str(WORK))
from scgptmini.data_collator import DataCollator  # noqa: E402
from scgptmini.model.model import TransformerModel  # noqa: E402

# ---- 2. the whole-human checkpoint (scGPT README, "whole-human (recommended)")
mdir = WORK / "scGPT_human"
if not (mdir / "best_model.pt").exists():
    import gdown
    gdown.download_folder(id="1oWh_-ZRdhtoGQ2Fw24HP41FgLoomVo-y", output=str(mdir), quiet=False)
print("checkpoint files:", sorted(os.listdir(mdir)), flush=True)
cfg = json.load(open(mdir / "args.json"))
vocab = json.load(open(mdir / "vocab.json"))
for tok in ["<pad>", "<cls>", "<eoc>"]:
    if tok not in vocab:
        vocab[tok] = len(vocab)

dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = TransformerModel(
    ntoken=len(vocab), d_model=cfg["embsize"], nhead=cfg["nheads"], d_hid=cfg["d_hid"], nlayers=cfg["nlayers"],
    nlayers_cls=cfg["n_layers_cls"], n_cls=1, vocab=vocab, dropout=cfg["dropout"], pad_token=cfg["pad_token"],
    pad_value=cfg["pad_value"], do_mvc=True, do_dab=False, use_batch_labels=False, domain_spec_batchnorm=False,
    explicit_zero_prob=False, use_fast_transformer=False, fast_transformer_backend="flash", pre_norm=False)
params = torch.load(mdir / "best_model.pt", map_location="cpu")
params = {k.replace("Wqkv.", "in_proj_"): v for k, v in params.items()}  # as scgpt.utils.load_pretrained
own = model.state_dict()
ok = {k: v for k, v in params.items() if k in own and v.shape == own[k].shape}
own.update(ok)
model.load_state_dict(own)
missing = [k for k in model.state_dict() if k not in ok]
print(f"loaded {len(ok)}/{len(model.state_dict())} tensors; not loaded: {missing}", flush=True)
assert all(k.startswith(("cls_decoder", "mvc_decoder", "decoder", "grad_reverse", "dsbn")) for k in missing) \
    or not missing, "encoder weights failed to load"
model.to(dev).eval()

# ---- 3. data -> tokens, exactly as get_batch_cell_embeddings does
z = np.load(IN, allow_pickle=True)
X = sp.csr_matrix((z["data"], z["indices"], z["indptr"]), shape=tuple(z["shape"]))
symbols = z["symbols"].astype(str)
in_vocab = np.array([s in vocab for s in symbols])
gene_ids = np.array([vocab[s] for s in symbols[in_vocab]], dtype=np.int64)
X = X[:, np.flatnonzero(in_vocab)].tocsr()
print(f"{X.shape[0]} cells; {in_vocab.sum()}/{len(symbols)} genes in the scGPT vocabulary", flush=True)

collator = DataCollator(do_padding=True, pad_token_id=vocab[cfg["pad_token"]], pad_value=cfg["pad_value"],
                        do_mlm=False, do_binning=True, max_length=1200, sampling=True, keep_first_n_tokens=1)
out = np.zeros((X.shape[0], cfg["embsize"]), np.float32)
bs, t0 = 64, time.time()
with torch.no_grad(), torch.autocast("cuda", enabled=dev.type == "cuda"):
    for b in range(0, X.shape[0], bs):
        ex = []
        for i in range(b, min(b + bs, X.shape[0])):
            lo, hi = X.indptr[i], X.indptr[i + 1]
            genes = np.insert(gene_ids[X.indices[lo:hi]], 0, vocab["<cls>"])
            vals = np.insert(X.data[lo:hi].astype(np.float32), 0, cfg["pad_value"])
            ex.append({"id": i, "genes": torch.from_numpy(genes).long(), "expressions": torch.from_numpy(vals).float()})
        d = collator(ex)
        g = d["gene"].to(dev)
        emb = model._encode(g, d["expr"].to(dev), src_key_padding_mask=g.eq(vocab[cfg["pad_token"]]), batch_labels=None)
        out[b:b + len(ex)] = emb[:, 0, :].float().cpu().numpy()
        if (b // bs) % 100 == 0:
            print(f"{b + len(ex)}/{X.shape[0]} cells, {time.time() - t0:.0f}s", flush=True)
out = out / np.linalg.norm(out, axis=1, keepdims=True)
np.save(WORK / "emb_scgpt_human.npy", out)
shutil.rmtree(mdir, ignore_errors=True)  # keep only the embedding in the kernel output
shutil.rmtree(pkg, ignore_errors=True)
print(f"done in {time.time() - t0:.0f}s -> emb_scgpt_human.npy {out.shape}", flush=True)
