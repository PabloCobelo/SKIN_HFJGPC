"""
Train YOLOv8 on the prepared HAM10000 YOLO dataset.

Run:
    python scripts/train.py

Results (weights, metrics CSVs, plots) go to results/train/
"""

from pathlib import Path
from ultralytics import YOLO

BASE_DIR    = Path(__file__).resolve().parents[1]
DATASET_CFG = BASE_DIR / "data" / "yolo_dataset" / "dataset.yaml"
MODELS_DIR  = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"

# ── hyper-parameters ──────────────────────────────────────────────────────────
MODEL_SIZE  = "yolov8n"   # nano – fastest; swap to yolov8s/m for better accuracy
EPOCHS      = 50
IMG_SIZE    = 224          # HAM10000 images are 600×450; 224 keeps training fast
BATCH       = 16
WORKERS     = 4
DEVICE      = "cpu"        # change to 0 (or "cuda:0") if GPU is available
# ─────────────────────────────────────────────────────────────────────────────


def main():
    assert DATASET_CFG.exists(), f"Run prepare_dataset.py first. Not found: {DATASET_CFG}"

    MODELS_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    checkpoint = RESULTS_DIR / "train" / "weights" / "last.pt"

    if checkpoint.exists():
        print(f"Resuming from checkpoint: {checkpoint}")
        model = YOLO(str(checkpoint))
        results = model.train(resume=True)
    else:
        print("Starting training from scratch…")
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
        print(f"\nBest weights saved → {dest}")

    print(f"\nAll results at: {results.save_dir}")


if __name__ == "__main__":
    main()
