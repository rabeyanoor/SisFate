"""Ensembl -> HGNC symbol mapping and cell-cycle gene lists."""
from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd

HGNC_URL = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"

# Tirosh et al. 2016 cell-cycle genes (the lists Seurat/scanpy tutorials use), with current HGNC
# symbols added next to retired aliases (MLF1IP->CENPU, FAM64A->PIMREG, HN1->JPT1).
S_GENES = """MCM5 PCNA TYMS FEN1 MCM2 MCM4 RRM1 UNG GINS2 MCM6 CDCA7 DTL PRIM1 UHRF1 MLF1IP CENPU HELLS
RFC2 RPA2 NASP RAD51AP1 GMNN WDR76 SLBP CCNE2 UBR7 POLD3 MSH2 ATAD2 RAD51 RRM2 CDC45 CDC6 EXO1 TIPIN
DSCC1 BLM CASP8AP2 USP1 CLSPN POLA1 CHAF1B BRIP1 E2F8""".split()
G2M_GENES = """HMGB2 CDK1 NUSAP1 UBE2C BIRC5 TPX2 TOP2A NDC80 CKS2 NUF2 CKS1B MKI67 TMPO CENPF TACC3 FAM64A
PIMREG SMC4 CCNB2 CKAP2L CKAP2 AURKB BUB1 KIF11 ANP32E TUBB4B GTSE1 KIF20B HJURP CDCA3 HN1 JPT1 CDC20
TTK CDC25C KIF2C RANGAP1 NCAPD2 DLGAP5 CDCA2 CDCA8 ECT2 KIF23 HMMR AURKA PSRC1 ANLN LBR CKAP5 CENPE
CTCF NEK2 G2E3 GAS2L3 CBX5 CENPA""".split()


def ensembl_to_symbol(ref_dir: Path) -> dict[str, str]:
    path = Path(ref_dir) / "hgnc_complete_set.txt"
    if not path.exists():
        urllib.request.urlretrieve(HGNC_URL, path)
    hgnc = pd.read_csv(path, sep="\t", usecols=["symbol", "ensembl_gene_id"], dtype=str).dropna()
    return dict(zip(hgnc["ensembl_gene_id"], hgnc["symbol"]))


def annotate_symbols(var: pd.DataFrame, ref_dir: Path) -> pd.DataFrame:
    """Add a `symbol` column; genes without an HGNC entry keep their Ensembl id."""
    try:
        mapping = ensembl_to_symbol(ref_dir)
    except Exception as exc:  # offline: fall back to Ensembl ids
        print(f"[genes] HGNC mapping unavailable ({exc}); using Ensembl ids as symbols")
        mapping = {}
    var = var.copy()
    var["symbol"] = [mapping.get(e, e) for e in var.index]
    var["mt"] = var["symbol"].str.startswith("MT-")
    var["ribo"] = var["symbol"].str.match(r"^RP[SL]\d")
    return var
