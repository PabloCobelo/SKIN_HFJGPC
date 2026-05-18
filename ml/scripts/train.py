"""
Train YOLOv8 on the prepared HAM10000 YOLO dataset.

Run:
    python ml/scripts/train.py            # train from scratch
    python ml/scripts/train.py --resume  # resume from last checkpoint

Results (weights, metrics CSVs, plots) go to results/train/
"""

import argparse
from pathlib import Path
from ultralytics import YOLO

ML_DIR      = Path(__file__).resolve().parents[1]   # ml/
ROOT_DIR    = ML_DIR.parent                          # project root
DATASET_CFG = ML_DIR / "data" / "yolo_dataset" / "dataset.yaml"
MODELS_DIR  = ROOT_DIR / "backend" / "models"
RESULTS_DIR = ML_DIR / "results"

# ── hyper-parameters ──────────────────────────────────────────────────────────
MODEL_SIZE  = "yolov8s"   # nano – fastest; swap to yolov8s/m for better accuracy
EPOCHS      = 50
IMG_SIZE    = 224          # HAM10000 images are 600×450; 224 keeps training fast
BATCH       = 16
WORKERS     = 4
DEVICE      = 0            # RTX 4050; use "cpu" if CUDA not available
# ─────────────────────────────────────────────────────────────────────────────


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
