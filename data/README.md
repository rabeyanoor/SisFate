# Data

The data are public and are not stored in this repository. `scripts/00_download.sh`,
`scripts/00b_download_external.sh` and `scripts/00c_download_schaff.sh` download them into this folder
(about 6 GB once processed). Every data set is analysed on its own; they are never merged into one training
set, because they come from different cell lines, barcoding protocols and labels (see below).

| Data set | Source | What it contains | Role in the study |
|---|---|---|---|
| ReSisTrace (Dai et al. 2024) | GEO [GSE223003](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE223003) | Kuramochi ovarian cancer cells; carboplatin, olaparib, NK-cell and untreated control arms, two replicates each; 32,642 labelled pre-treatment cells labelled by their sister's fate | Main data set: all models are trained and evaluated here, with families kept together |
| Multi-treatment melanoma (Schaff et al. 2026) | GEO [GSE279162](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE279162) | WM989 melanoma cells; 7,165 untreated cells from 1,359 lineages, each labelled under six treatments | Second lineage system: clone size against expression |
| PC9 osimertinib, Watermelon (Oren et al. 2021) | GEO [GSE150949](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE150949) | 5,087 barcoded day-0 cells from 2,993 lineages | External check; zero-shot transfer of ReSisTrace models |
| Triple-negative breast cancer, afatinib (Pellecchia et al. 2024) | GEO [GSE228382](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE228382) and figshare [24787458](https://doi.org/10.6084/m9.figshare.24787458) | 1,541 untreated barcoded cells from 448 lineages; lineage annotations from the authors' Seurat object | External check; zero-shot transfer |
| Ovarian cancer patients before and after chemotherapy (Zhang et al. 2022) | GEO [GSE165897](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE165897) | 8,806 malignant cells from 11 patients; clinical table from the paper (`external/zhang2022/`) | Do the signatures rise after treatment? |
| TCGA-OV | [UCSC Xena](https://xenabrowser.net/datapages/?cohort=TCGA%20Ovarian%20Cancer%20(OV)) | RNA-seq and curated survival of 303 primary tumours | Do the signatures predict survival? |

Folders created by the scripts: `raw/` (downloads), `processed/` (AnnData objects, principal components,
foundation-model embeddings), `external/` (the four external data sets), `ref/` (TCGA files).

The processed objects and the Geneformer and scGPT embeddings, which need a GPU to recompute, are prepared for
deposit on Zenodo (CC BY 4.0) so that the analyses can be rerun without the GPU steps.
