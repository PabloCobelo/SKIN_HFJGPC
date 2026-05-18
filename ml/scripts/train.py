"""
Train YOLOv8 on the prepared HAM10000 YOLO dataset.

Run:
    python ml/scripts/train.py            # train from scratch
    python ml/scripts/train.py --resume  # resume from last checkpoint

Results (weights, metrics CSVs, plots) go to results/train/
"""

import argparse
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from ultralytics import YOLO

ML_DIR      = Path(__file__).resolve().parents[1]   # ml/
ROOT_DIR    = ML_DIR.parent                          # project root
DATASET_CFG = ML_DIR / "data" / "yolo_dataset" / "dataset.yaml"
META_CSV    = ML_DIR / "data" / "ham1000" / "HAM10000_metadata"
MODELS_DIR  = ROOT_DIR / "backend" / "models"
RESULTS_DIR = ML_DIR / "results"

# ── hyper-parameters ──────────────────────────────────────────────────────────
MODEL_SIZE  = "yolov8n"   # nano – fastest; swap to yolov8s/m for better accuracy
EPOCHS      = 50
IMG_SIZE    = 224          # HAM10000 images are 600×450; 224 keeps training fast
BATCH       = 16
WORKERS     = 4
DEVICE      = "0"        # change to 0 (or "cuda:0") if GPU is available
CLASSES     = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
# ─────────────────────────────────────────────────────────────────────────────


def _class_weights() -> torch.Tensor:
    df = pd.read_csv(META_CSV, sep=None, engine="python")
    counts = np.array([df["dx"].value_counts().get(c, 1) for c in CLASSES], dtype=float)
    weights = counts.sum() / (len(counts) * counts)
    weights /= weights.mean()
    print("Class weights (inverse frequency):")
    for cls, w in zip(CLASSES, weights):
        print(f"  {cls:6s}: {w:.3f}")
    return torch.tensor(weights, dtype=torch.float32)


def _make_inject_callback(weights: torch.Tensor):
    applied = [False]

    def inject(trainer):
        if applied[0]:
            return
        crit = getattr(trainer.model, "criterion", None)
        if crit is not None and hasattr(crit, "BCEcls"):
            crit.BCEcls = nn.BCEWithLogitsLoss(
                pos_weight=weights.to(trainer.device), reduction="none"
            )
            applied[0] = True
            print("✓ Per-class weights applied to BCE loss")

    return inject


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true",
                        help="Resume training from results/train/weights/last.pt")
    args = parser.parse_args()

    assert DATASET_CFG.exists(), f"Run prepare_dataset.py first. Not found: {DATASET_CFG}"

    MODELS_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    if args.resume:
        checkpoint = RESULTS_DIR / "train" / "weights" / "last.pt"
        assert checkpoint.exists(), f"No checkpoint found at {checkpoint}"
        print(f"Resuming from checkpoint: {checkpoint}")
        model = YOLO(str(checkpoint))
        results = model.train(resume=True)
    else:
        print(f"Starting training with {MODEL_SIZE} on HAM10000...")
        model = YOLO(f"{MODEL_SIZE}.pt")
        model.add_callback("on_train_batch_end", _make_inject_callback(_class_weights()))
        results = model.train(
            data    = str(DATASET_CFG),
            epochs  = EPOCHS,
            imgsz   = IMG_SIZE,
            batch   = BATCH,
            workers = WORKERS,
            device  = DEVICE,
            project = str(RESULTS_DIR),
            name    = "train",
            exist_ok= True,
            patience= 15,
            plots   = True,
            save    = True,
            verbose = False,
        )

    # copy best weights to models/
    best = Path(results.save_dir) / "weights" / "best.pt"
    if best.exists():
        import shutil
        dest = MODELS_DIR / "best.pt"
        shutil.copy2(best, dest)
        print(f"\nBest weights saved -> {dest}")

    print(f"\nAll results at: {results.save_dir}")


if __name__ == "__main__":
    main()
