# Export a Seurat object's metadata and raw counts to plain files (so Python never needs R).
# Uses raw slot access, so it works on old (Seurat v3) objects without installing Seurat itself.
# usage: Rscript scripts/export_seurat.R <in.rds> <out_dir>
suppressPackageStartupMessages({library(Matrix); library(data.table)})
args <- commandArgs(trailingOnly = TRUE)
obj <- readRDS(args[1])
dir.create(args[2], showWarnings = FALSE, recursive = TRUE)
meta <- slot(obj, "meta.data")
fwrite(cbind(cell = rownames(meta), meta), file.path(args[2], "meta.csv.gz"))
assays <- slot(obj, "assays")
cat("assays:", paste(names(assays), collapse = ", "), "\n")
a <- assays[[slot(obj, "active.assay")]]
att <- attributes(a)  # S4 slots are attributes; avoids needing the Seurat class definition
counts <- if (!is.null(att$counts) && length(att$counts) > 0) att$counts else att$layers$counts
writeMM(counts, file.path(args[2], "counts.mtx"))
fwrite(data.table(gene = rownames(counts)), file.path(args[2], "genes.csv"))
fwrite(data.table(cell = colnames(counts)), file.path(args[2], "cells.csv"))
cat("cells:", ncol(counts), " genes:", nrow(counts), "\n")
cat("meta columns:", paste(colnames(meta), collapse = ", "), "\n")
