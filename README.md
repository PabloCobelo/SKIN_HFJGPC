# Epidermix — Detección de Lesiones Cutáneas con YOLOv8

App móvil y web que detecta 7 tipos de lesiones dermatoscópicas usando un modelo YOLOv8 entrenado sobre HAM10000.

**Stack:** Flutter (móvil + web) · FastAPI · YOLOv8 · Docker

---

## Requisitos previos

| Herramienta | Versión mínima | Instalación |
|-------------|---------------|-------------|
| Python | 3.13 | [python.org](https://www.python.org/downloads/) |
| uv | cualquiera | `pip install uv` |
| Flutter SDK | 3.3+ | [flutter.dev](https://docs.flutter.dev/get-started/install) |
| Docker Desktop | cualquiera | [docker.com](https://www.docker.com/products/docker-desktop/) *(solo para backend con Docker)* |

> **Windows:** asegúrate de que `python`, `uv` y `flutter` están en el PATH.

---

## Estructura del repositorio

```
SKIN_HFJGPC/
├── backend/          # API REST (FastAPI + YOLOv8)
│   ├── app/
│   ├── models/best.pt   # pesos entrenados (ver sección ML)
│   ├── requirements.txt
│   └── Dockerfile
├── mobile/           # App Flutter (Android, iOS, Web)
├── ml/               # Pipeline de entrenamiento (offline)
│   ├── scripts/
│   ├── skin_lesion_pipeline.ipynb
│   └── yolov8n.pt    # pesos base preentrenados
└── docker-compose.yml
```

---

## 1 — Pipeline ML (entrenamiento del modelo)

> Omite esta sección si ya tienes `backend/models/best.pt`.

### 1.1 Crear entorno Python

```bash
uv venv --python 3.13 .venv313
# Windows
.venv313\Scripts\activate
# macOS / Linux
source .venv313/bin/activate

uv pip install ultralytics opencv-python pillow numpy tqdm scikit-learn pyyaml
```

### 1.2 Descargar HAM10000

**Opción A — Descarga automática** (~3.5 GB):
```bash
python ml/scripts/download_ham10000.py
```

**Opción B — Descarga manual** desde [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DBW86T).
Coloca los archivos en:
```
ml/data/ham1000/
  HAM10000_metadata.csv
  HAM10000_images_part_1/         ← imágenes ISIC_*.jpg
  HAM10000_images_part_2/         ← imágenes ISIC_*.jpg
  HAM10000_segmentations_lesion_tschandl/
    HAM10000_segmentations_lesion_tschandl/  ← máscaras ISIC_*_segmentation.png
```

### 1.3 Preparar dataset

```bash
python ml/scripts/prepare_dataset.py
```

Genera `ml/data/yolo_dataset/` con el split 80/20 estratificado en formato YOLO.

### 1.4 Entrenar

```bash
python ml/scripts/train.py
```

Para reanudar desde un checkpoint anterior:
```bash
python ml/scripts/train.py --resume
```

Al terminar, copia automáticamente los mejores pesos a `backend/models/best.pt`.

### 1.5 Evaluar

```bash
python ml/scripts/evaluate.py
```

Genera en `ml/results/eval/`: matriz de confusión, métricas por clase y mAP.

> También puedes ejecutar todo el pipeline desde el notebook `ml/skin_lesion_pipeline.ipynb` (abrir con el kernel **Epidermix (Python 3.13)**).

---

## 2 — Backend (API REST)

El backend expone `POST /api/v1/predict` — recibe una imagen y devuelve las detecciones en JSON.

Asegúrate de que `backend/models/best.pt` existe antes de arrancar.

### Opción A — Docker (recomendado)

```bash
docker-compose up --build
```

El API queda disponible en `http://localhost:8000`.

### Opción B — Local con uv

```bash
uv venv --python 3.13 .venv313
# Windows
.venv313\Scripts\activate
# macOS / Linux
source .venv313/bin/activate

uv pip install -r backend/requirements.txt

cd backend
uvicorn app.main:app --reload --port 8000
```

> **Importante:** ejecuta `uvicorn` desde dentro de `backend/`, no desde la raíz del proyecto.

Documentación interactiva: `http://localhost:8000/docs`

---

## 3 — App móvil / web (Flutter)

### 3.1 Instalar dependencias

```bash
cd mobile
flutter pub get
```

### 3.2 Configurar la URL del backend

Edita `mobile/lib/services/api_service.dart` y ajusta `_baseUrl` según tu caso:

| Escenario | URL |
|-----------|-----|
| Emulador Android | `http://10.0.2.2:8000` *(por defecto)* |
| Navegador web (mismo equipo) | `http://localhost:8000` |
| Dispositivo físico / red local | `http://<IP-de-tu-máquina>:8000` |

### 3.3 Ejecutar

**Navegador web (Edge o Chrome):**
```bash
cd mobile
flutter run -d edge
# o
flutter run -d chrome
```

**Emulador Android:**
```bash
cd mobile
flutter run -d android
```

**Dispositivo físico:**
```bash
flutter devices          # ver IDs disponibles
flutter run -d <device-id>
```

---

## 4 — Flujo completo de uso

1. Arranca el backend (`docker-compose up` o `uvicorn`).
2. Lanza la app Flutter.
3. Pulsa el botón de cámara o galería y selecciona una imagen dermatoscópica.
4. La app envía la imagen al backend y muestra las detecciones con bounding boxes y un panel de información clínica.
5. Si la lesión detectada es de riesgo alto (melanoma, carcinoma basocelular o queratosis actínica), aparece un botón para solicitar cita en el SERGAS.

---

## Clases detectadas

| ID | Código | Nombre | Riesgo |
|----|--------|--------|--------|
| 0 | akiec | Queratosis Actínica | Alto |
| 1 | bcc | Carcinoma Basocelular | Alto |
| 2 | bkl | Queratosis Benigna | Bajo |
| 3 | df | Dermatofibroma | Bajo |
| 4 | mel | Melanoma | Alto |
| 5 | nv | Nevo Melanocítico | Bajo |
| 6 | vasc | Lesión Vascular | Bajo |

---

> **Aviso legal:** Este sistema es orientativo y no reemplaza el diagnóstico médico profesional.
