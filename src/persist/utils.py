"""Config loading, seeding, logging and the append-only results table."""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import random
import time
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | os.PathLike | None = None) -> dict:
    path = Path(path) if path else ROOT / "configs" / "default.yaml"
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    for key, val in cfg["paths"].items():
        p = Path(val)
        cfg["paths"][key] = p if p.is_absolute() else ROOT / p
        cfg["paths"][key].mkdir(parents=True, exist_ok=True)
    cfg["_hash"] = config_hash(cfg)
    return cfg


def config_hash(cfg: dict) -> str:
    clean = {k: v for k, v in cfg.items() if not k.startswith("_") and k != "paths"}
    return hashlib.sha1(json.dumps(clean, sort_keys=True, default=str).encode()).hexdigest()[:8]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
    except ImportError:
        pass


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s", datefmt="%H:%M:%S"
    )
    return logging.getLogger(name)


RESULT_FIELDS = [
    "timestamp", "config_hash", "experiment", "model", "features", "cc_mode", "split",
    "train", "test", "fold", "seed", "shuffled", "n_test", "n_pos", "prevalence",
    "auroc", "auroc_lo", "auroc_hi", "auprc", "auprc_lo", "auprc_hi", "auprc_lift",
    "within_cluster_auroc", "notes",
]


def append_results(rows: list[dict], cfg: dict, filename: str = "results.csv") -> Path:
    """Append metric rows to results/<filename>; every run is kept (never overwritten)."""
    path = Path(cfg["paths"]["results_dir"]) / filename
    new = not path.exists()
    with open(path, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=RESULT_FIELDS, extrasaction="ignore")
        if new:
            writer.writeheader()
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        for r in rows:
            writer.writerow({"timestamp": stamp, "config_hash": cfg["_hash"], **r})
    return path
