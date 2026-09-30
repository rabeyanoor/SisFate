"""Do the ReSisTrace signatures mark cancer cells that persist through chemotherapy in patients?

Data: Zhang et al. (2022, Sci Adv) scRNA-seq of 11 high-grade serous ovarian cancer patients sampled before
(treatment-naive, TN) and after three cycles of neoadjuvant platinum-taxane chemotherapy (post-NACT, PN); GEO
GSE165897. Clinical data (platinum-free interval, chemotherapy response score) are from their Table 1
(data/external/zhang2022/clinical_table1.csv).

Hypotheses, fixed before looking at the results:
  H1  If pre-resistant states are selected by carboplatin-based chemotherapy in patients, malignant cells
      after NACT score higher than treatment-naive cells of the same patient on the carboplatin signatures
      (whole contrast and drug-specific) and on the fitness signature.
  H2  This shift exceeds that of random gene sets matched in size and mean expression (NACT changes much
      of the transcriptome, so a raw shift alone is not evidence).
Exploratory (n = 11, reported without claims): patient-level scores vs platinum-free interval.
Sensitivity: the five patients whose two samples came from the same anatomical site.

Scoring: malignant (EOC) cells only; log-normalised (10,000 counts per cell); each gene z-scored within
patient across that patient's TN and PN cells; score = mean z of up genes − mean z of down genes.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--n-random", type=int, default=200)
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("patient_nact")
D = Path("data/external/zhang2022")
R = Path(cfg["paths"]["results_dir"])
SIGS = ["fitness_Control", "all_Carboplatin", "specific_Carboplatin", "specific_Olaparib", "specific_NK"]

info = pd.read_csv(D / "GSE165897_cellInfo_HGSOC.tsv.gz", sep="\t", index_col=0)
info = info[info["cell_type"] == "EOC"]
cache = D / "eoc_counts.npz"
if cache.exists():
    z = np.load(cache, allow_pickle=True)
    X, genes, cells = sp.csr_matrix((z["data"], z["indices"], z["indptr"]), shape=z["shape"]), z["genes"], z["cells"]
else:
    header = pd.read_csv(D / "GSE165897_UMIcounts_HGSOC.tsv.gz", sep="\t", nrows=0).columns
    keep = [c for c in header if c in info.index]
    parts, genes = [], []
    for ch in pd.read_csv(D / "GSE165897_UMIcounts_HGSOC.tsv.gz", sep="\t", index_col=0, usecols=[header[0]] + keep,
                          chunksize=2000):
        parts.append(sp.csr_matrix(ch.to_numpy(np.float32).T))
        genes += list(ch.index)
    X, genes, cells = sp.hstack(parts).tocsr(), np.array(genes), np.array(keep)
    np.savez_compressed(cache, data=X.data, indices=X.indices, indptr=X.indptr, shape=X.shape, genes=genes, cells=cells)
info = info.loc[cells]
log.info(f"{X.shape[0]} malignant cells x {X.shape[1]} genes; {info['patient_id'].nunique()} patients")

lib = np.asarray(X.sum(1)).ravel()
L = sp.diags(1e4 / lib) @ X
L.data = np.log1p(L.data)
L = L.tocsc()
detected = np.asarray((X > 0).mean(0)).ravel()
expressed = np.flatnonzero(detected >= 0.01)
gidx = {g: i for i, g in enumerate(genes)}
mean_expr = np.asarray(L.mean(0)).ravel()
patients = info["patient_id"].to_numpy()
phase = (info["treatment_phase"] == "post-NACT").to_numpy()


def zscore_within_patient(cols):
    M = L[:, cols].toarray()
    for p in np.unique(patients):
        m = patients == p
        M[m] = (M[m] - M[m].mean(0)) / (M[m].std(0) + 1e-8)
    return M


def patient_shift(score):
    """Per patient: mean PN score − mean TN score (scores are within-patient z, so in s.d.-like units)."""
    return pd.Series({p: score[(patients == p) & phase].mean() - score[(patients == p) & ~phase].mean()
                      for p in np.unique(patients)})


clin0 = pd.read_csv(D / "clinical_table1.csv").set_index("patient_id")
same_site = (clin0["location_tn"] == clin0["location_pn"]).reindex(sorted(np.unique(patients))).to_numpy()
sig = json.load(open(R / "interpret" / "signatures.json"))
rng = np.random.default_rng(cfg["seed"])
bins = pd.qcut(mean_expr[expressed], 20, labels=False, duplicates="drop")
rows, per_patient = [], []
for name in SIGS:
    up = [gidx[g] for g in sig[name]["up"] if g in gidx and gidx[g] in set(expressed)]
    dn = [gidx[g] for g in sig[name]["down"] if g in gidx and gidx[g] in set(expressed)]
    Zu, Zd = zscore_within_patient(up), zscore_within_patient(dn)
    score = Zu.mean(1) - Zd.mean(1)
    shift = patient_shift(score)
    # null: random up/down sets of the same sizes, matched to the expression bins of the real genes
    pos = {g: k for k, g in enumerate(expressed)}

    def matched(idx):
        out = []
        for g in idx:
            pool = expressed[bins == bins[pos[g]]]
            out.append(rng.choice(pool))
        return out

    null_med = np.empty(args.n_random)
    null_shift = np.empty((args.n_random, len(shift)))
    for k in range(args.n_random):
        s = zscore_within_patient(matched(up)).mean(1) - zscore_within_patient(matched(dn)).mean(1)
        ns = patient_shift(s)
        null_shift[k] = ns.to_numpy()
        null_med[k] = ns.median()
    w = stats.wilcoxon(shift.to_numpy())
    pct = (null_shift < shift.to_numpy()[None, :]).mean(0)  # per-patient percentile vs matched random sets
    rows.append({"signature": name, "n_up": len(up), "n_down": len(dn), "n_patients": len(shift),
                 "median_shift": shift.median(), "n_positive": int((shift > 0).sum()),
                 "wilcoxon_p": w.pvalue, "null_median_shift_mean": null_med.mean(),
                 "null_median_shift_sd": null_med.std(ddof=1),
                 "p_vs_random_sets": (np.sum(null_med >= shift.median()) + 1) / (args.n_random + 1),
                 "p_vs_random_sets_two_sided": (np.sum(np.abs(null_med - null_med.mean())
                                                       >= abs(shift.median() - null_med.mean())) + 1) / (args.n_random + 1),
                 "median_shift_same_site": shift[same_site].median(),
                 "n_positive_same_site": int((shift[same_site] > 0).sum()), "n_same_site": int(same_site.sum()),
                 "n_patients_above_95pct_random": int((pct > 0.95).sum())})
    for p, v in shift.items():
        per_patient.append({"signature": name, "patient_id": p, "shift_pn_minus_tn": v,
                            "percentile_vs_random": pct[list(shift.index).index(p)]})
    log.info(f"{name}: median shift {shift.median():+.3f}, {int((shift > 0).sum())}/{len(shift)} up, "
             f"Wilcoxon p {w.pvalue:.3g}, random-set p {rows[-1]['p_vs_random_sets']:.3g}")

res = pd.DataFrame(rows)
pp = pd.DataFrame(per_patient)
clin = pd.read_csv(D / "clinical_table1.csv")
pp = pp.merge(clin, on="patient_id", how="left")
# exploratory: does the shift or the TN level relate to the platinum-free interval? (n = 11)
expl = []
for name, d in pp.groupby("signature"):
    r = stats.spearmanr(d["shift_pn_minus_tn"], d["pfi_days"])
    expl.append({"signature": name, "spearman_shift_vs_pfi": r.statistic, "p": r.pvalue})
res = res.merge(pd.DataFrame(expl), on="signature")
res.to_csv(R / "patient_nact.csv", index=False)
pp.to_csv(R / "patient_nact_per_patient.csv", index=False)
print(res.round(4).to_string(index=False))
