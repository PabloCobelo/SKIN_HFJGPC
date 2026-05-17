# HAM10000 – Skin Lesion Detection with YOLOv8

## Setup

```bash
pip install -r requirements.txt
```

## Dataset

**Option A — Automatic download** (~3.5 GB, no credentials required):
```bash
python ml/scripts/download_ham10000.py
```

**Option B — Manual download** from https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DBW86T

Place files under `ml/data/ham1000/`:
```
ml/data/ham1000/
  HAM10000_metadata                         ← CSV sin extensión
  HAM10000_images_part_1/                   ← imágenes ISIC_*.jpg
  HAM10000_images_part_2/                   ← imágenes ISIC_*.jpg
  HAM10000_segmentations_lesion_tschandl/
    HAM10000_segmentations_lesion_tschandl/ ← máscaras ISIC_*_segmentation.png
```

## Workflow

### 1 – Download dataset
```bash
python ml/scripts/download_ham10000.py
```

### 2 – Prepare dataset
```bash
python ml/scripts/prepare_dataset.py
```

### 3 – Train YOLOv8
```bash
python ml/scripts/train.py
```

### 4 – Evaluate
```bash
python ml/scripts/evaluate.py
```

### 5 – Desktop application
```bash
python app/main.py
```

## Classes
| ID | Code  | Description               |
|----|-------|---------------------------|
| 0  | akiec | Actinic Keratosis         |
| 1  | bcc   | Basal Cell Carcinoma      |
| 2  | bkl   | Benign Keratosis          |
| 3  | df    | Dermatofibroma            |
| 4  | mel   | Melanoma                  |
| 5  | nv    | Melanocytic Nevus         |
| 6  | vasc  | Vascular Lesion           |
