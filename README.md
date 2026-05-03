# HAM10000 – Skin Lesion Detection with YOLOv8

## Setup

```bash
pip install -r requirements.txt
```

## Dataset

Download from https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DBW86T

Place files under `data/ham1000/` (estructura real del dataset de Harvard):
```
data/ham1000/
  HAM10000_metadata                         ← CSV sin extensión
  HAM10000_images_part_1/                   ← imágenes ISIC_*.jpg
  HAM10000_images_part_2/                   ← imágenes ISIC_*.jpg
  HAM10000_segmentations_lesion_tschandl/
    HAM10000_segmentations_lesion_tschandl/ ← máscaras ISIC_*_segmentation.png
```

## Workflow

### 1 – Prepare dataset
```bash
python scripts/prepare_dataset.py
```

### 2 – Train YOLOv8
```bash
python scripts/train.py
```

### 3 – Evaluate
```bash
python scripts/evaluate.py
```

### 4 – Desktop application
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
