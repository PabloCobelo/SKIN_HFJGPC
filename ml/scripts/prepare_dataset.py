"""
Converts HAM10000 dataset to YOLO format.

Actual structure under ml/data/ham1000/:
  HAM10000_metadata              (CSV, no extension)
  HAM10000_images_part_1/        (ISIC_*.jpg)
  HAM10000_images_part_2/        (ISIC_*.jpg)
  HAM10000_segmentations_lesion_tschandl/
    HAM10000_segmentations_lesion_tschandl/   (ISIC_*_segmentation.png)

Output under ml/data/yolo_dataset/:
  images/train/, images/val/
  labels/train/, labels/val/
  dataset.yaml
"""

import shutil
import cv2
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import yaml

# ── config ────────────────────────────────────────────────────────────────────
ML_DIR       = Path(__file__).resolve().parents[1]   # ml/
HAM_DIR      = ML_DIR / "data" / "ham1000"
IMG_DIRS     = [
    HAM_DIR / "HAM10000_images_part_1",
    HAM_DIR / "HAM10000_images_part_2",
    HAM_DIR,   # fallback: imágenes sueltas en ham1000/
]
# Support both nested (manual download) and flat (Dataverse download) structures
_seg_nested  = (HAM_DIR / "HAM10000_segmentations_lesion_tschandl"
                        / "HAM10000_segmentations_lesion_tschandl")
_seg_flat    = HAM_DIR / "HAM10000_segmentations_lesion_tschandl"
SEG_DIR      = _seg_nested if _seg_nested.exists() else _seg_flat
META_CSV     = HAM_DIR / "HAM10000_metadata"   # no .csv extension
OUT_DIR      = ML_DIR / "data" / "yolo_dataset"
VAL_SPLIT    = 0.2
RANDOM_SEED  = 42

CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
CLASS_TO_ID = {c: i for i, c in enumerate(CLASSES)}
# ──────────────────────────────────────────────────────────────────────────────


def bbox_from_mask(mask_path: Path):
    """Return (x_center, y_center, w, h) normalised [0,1] from a binary mask."""
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return None
    _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    coords = cv2.findNonZero(binary)
    if coords is None:
        return None
    x, y, w, h = cv2.boundingRect(coords)
    img_h, img_w = mask.shape
    return (
        (x + w / 2) / img_w,
        (y + h / 2) / img_h,
        w / img_w,
        h / img_h,
    )


def bbox_full_image(img_path: Path):
    """Fallback: bounding box = full image centre."""
    img = cv2.imread(str(img_path))
    if img is None:
        return None
    return (0.5, 0.5, 1.0, 1.0)


def make_dirs():
    for split in ("train", "val"):
        (OUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)


def write_yaml():
    cfg = {
        "path": str(OUT_DIR),
        "train": "images/train",
        "val":   "images/val",
        "nc":    len(CLASSES),
        "names": CLASSES,
    }
    with open(OUT_DIR / "dataset.yaml", "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)
    print(f"Saved dataset.yaml -> {OUT_DIR / 'dataset.yaml'}")


def find_image(img_id: str) -> Path | None:
    """Search for image across all available image folders."""
    for img_dir in [d for d in IMG_DIRS if d.exists()]:
        for ext in (".jpg", ".JPG", ".jpeg"):
            p = img_dir / f"{img_id}{ext}"
            if p.exists():
                return p
    return None


def main():
    assert META_CSV.exists(), f"Metadata not found: {META_CSV}"
    existing_img_dirs = [d for d in IMG_DIRS if d.exists()]
    assert existing_img_dirs, f"No image directories found. Checked: {IMG_DIRS}"

    make_dirs()
    write_yaml()

    df = pd.read_csv(META_CSV, sep=None, engine="python")  # auto-detect tab or comma
    # keep one row per image_id (some images appear multiple times due to same lesion)
    df = df.drop_duplicates(subset="image_id").reset_index(drop=True)

    # stratified split by class
    from sklearn.model_selection import train_test_split
    train_df, val_df = train_test_split(
        df, test_size=VAL_SPLIT, stratify=df["dx"], random_state=RANDOM_SEED
    )
    split_map = {row.image_id: "train" for _, row in train_df.iterrows()}
    split_map.update({row.image_id: "val"   for _, row in val_df.iterrows()})

    missing_imgs   = 0
    missing_masks  = 0
    processed      = 0

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing"):
        img_id   = row["image_id"]
        class_id = CLASS_TO_ID.get(row["dx"])
        if class_id is None:
            continue

        # find image across part_1 and part_2
        img_path = find_image(img_id)
        if img_path is None:
            missing_imgs += 1
            continue

        # compute bounding box (masks live in nested folder)
        mask_path = SEG_DIR / f"{img_id}_segmentation.png"
        if mask_path.exists():
            bbox = bbox_from_mask(mask_path)
        else:
            missing_masks += 1
            bbox = bbox_full_image(img_path)

        if bbox is None:
            continue

        split = split_map[img_id]
        x_c, y_c, w, h = bbox

        # copy image
        dst_img = OUT_DIR / "images" / split / img_path.name
        shutil.copy2(img_path, dst_img)

        # write label
        label_txt = OUT_DIR / "labels" / split / f"{img_id}.txt"
        with open(label_txt, "w") as f:
            f.write(f"{class_id} {x_c:.6f} {y_c:.6f} {w:.6f} {h:.6f}\n")

        processed += 1

    print(f"\nDone. Processed={processed}, missing images={missing_imgs}, "
          f"used full-image bbox for {missing_masks} samples.")
    print(f"Train: {len(train_df)}  Val: {len(val_df)}")


if __name__ == "__main__":
    main()
