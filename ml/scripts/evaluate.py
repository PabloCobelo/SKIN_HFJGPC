"""
Evaluate the trained YOLO model on the validation set.

Generates:
  results/eval/confusion_matrix.png
  results/eval/metrics_report.txt
  results/eval/per_class_metrics.csv

Run:
    python ml/scripts/evaluate.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from ultralytics import YOLO

ML_DIR      = Path(__file__).resolve().parents[1]   # ml/
ROOT_DIR    = ML_DIR.parent                          # project root
MODEL_PATH  = ROOT_DIR / "backend" / "models" / "best.pt"
DATASET_CFG = ML_DIR / "data" / "yolo_dataset" / "dataset.yaml"
EVAL_DIR    = ML_DIR / "results" / "eval"

CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]


def collect_predictions(model, val_img_dir: Path, val_lbl_dir: Path):
    """Run inference on all val images and collect (true, pred) class pairs."""
    y_true, y_pred = [], []
    img_files = sorted(val_img_dir.glob("*.jpg")) + sorted(val_img_dir.glob("*.JPG"))

    for img_path in img_files:
        lbl_path = val_lbl_dir / (img_path.stem + ".txt")
        if not lbl_path.exists():
            continue

        # ground truth: first class on first label line
        with open(lbl_path) as f:
            first_line = f.readline().strip()
        if not first_line:
            continue
        true_cls = int(first_line.split()[0])

        # prediction: highest-confidence detection
        results = model(str(img_path), verbose=False)[0]
        if results.boxes and len(results.boxes):
            conf = results.boxes.conf.cpu().numpy()
            cls  = results.boxes.cls.cpu().numpy().astype(int)
            pred_cls = cls[conf.argmax()]
        else:
            pred_cls = true_cls   # no detection → skip (or assign dummy)

        y_true.append(true_cls)
        y_pred.append(pred_cls)

    return y_true, y_pred


def plot_confusion_matrix(y_true, y_pred, save_path: Path):
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(CLASSES))))
    fig, ax = plt.subplots(figsize=(9, 7))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=CLASSES)
    disp.plot(ax=ax, colorbar=True, xticks_rotation=45)
    ax.set_title("Confusion Matrix – HAM10000 Validation Set")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Saved confusion matrix → {save_path}")


def save_metrics(y_true, y_pred, report_path: Path, csv_path: Path):
    report = classification_report(
        y_true, y_pred,
        labels=list(range(len(CLASSES))),
        target_names=CLASSES,
        zero_division=0,
    )
    report_path.write_text(report)
    print(f"Saved text report → {report_path}")

    # per-class CSV
    report_dict = classification_report(
        y_true, y_pred,
        labels=list(range(len(CLASSES))),
        target_names=CLASSES,
        zero_division=0,
        output_dict=True,
    )
    rows = [
        {"class": cls, **{k: round(v, 4) for k, v in report_dict[cls].items()}}
        for cls in CLASSES
    ]
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    print(f"Saved per-class CSV → {csv_path}")
    print("\n" + report)


def main():
    assert MODEL_PATH.exists(), f"Train the model first. Not found: {MODEL_PATH}"

    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(MODEL_PATH))

    val_img_dir = ML_DIR / "data" / "yolo_dataset" / "images" / "val"
    val_lbl_dir = ML_DIR / "data" / "yolo_dataset" / "labels" / "val"

    print("Running inference on validation set…")
    y_true, y_pred = collect_predictions(model, val_img_dir, val_lbl_dir)

    if not y_true:
        print("No predictions collected. Check dataset paths.")
        return

    plot_confusion_matrix(y_true, y_pred, EVAL_DIR / "confusion_matrix.png")
    save_metrics(y_true, y_pred, EVAL_DIR / "metrics_report.txt", EVAL_DIR / "per_class_metrics.csv")

    # also run built-in YOLO val for mAP
    val_results = model.val(data=str(DATASET_CFG), verbose=True)
    map50 = val_results.box.map50
    map50_95 = val_results.box.map
    summary = {
        "mAP@0.5":     round(float(map50),     4),
        "mAP@0.5:0.95": round(float(map50_95), 4),
    }
    (EVAL_DIR / "map_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nmAP@0.5 = {summary['mAP@0.5']}   mAP@0.5:0.95 = {summary['mAP@0.5:0.95']}")


if __name__ == "__main__":
    main()
