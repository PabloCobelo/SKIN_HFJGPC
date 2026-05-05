"""
Aplicación de visualización para el modelo HAM10000 YOLO.
Ejecutar: python app/main.py
Abre automáticamente en el navegador en http://localhost:7860
"""

import json
from pathlib import Path

import cv2
import gradio as gr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from ultralytics import YOLO

# ── rutas ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "best.pt"
EVAL_DIR   = BASE_DIR / "results" / "eval"
TRAIN_DIR  = BASE_DIR / "results" / "train"

CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
CLASS_NAMES = {
    "akiec": "Actinic Keratosis",
    "bcc":   "Basal Cell Carcinoma",
    "bkl":   "Benign Keratosis",
    "df":    "Dermatofibroma",
    "mel":   "Melanoma",
    "nv":    "Melanocytic Nevus",
    "vasc":  "Vascular Lesion",
}
COLOURS = [
    (230, 25,  75),  # akiec – rojo
    (60,  180, 75),  # bcc   – verde
    (255, 225, 25),  # bkl   – amarillo
    (67,  99,  216), # df    – azul
    (245, 130, 49),  # mel   – naranja
    (145, 30,  180), # nv    – morado
    (66,  212, 244), # vasc  – cyan
]

# ── modelo ────────────────────────────────────────────────────────────────────
model = None
if MODEL_PATH.exists():
    model = YOLO(str(MODEL_PATH))


# ── tab 1: inferencia ─────────────────────────────────────────────────────────

def run_inference(pil_img):
    if pil_img is None:
        return None, "Sube una imagen para analizar."
    if model is None:
        return pil_img, "⚠️ Modelo no encontrado. Ejecuta primero train.py."

    img_np = np.array(pil_img)
    results = model(img_np, verbose=False)[0]

    annotated = img_np.copy()
    lines = []

    if results.boxes and len(results.boxes):
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cls  = int(box.cls[0])
            conf = float(box.conf[0])
            colour = COLOURS[cls % len(COLOURS)]

            cv2.rectangle(annotated, (x1, y1), (x2, y2), colour, 3)
            label = f"{CLASSES[cls]} {conf:.0%}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), colour, -1)
            cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            lines.append(
                f"**{CLASS_NAMES.get(CLASSES[cls], CLASSES[cls])}**  \n"
                f"Confianza: `{conf:.1%}`  \n"
                f"Bbox: ({x1}, {y1}) → ({x2}, {y2})\n"
            )
    else:
        lines.append("No se detectaron lesiones.")

    return Image.fromarray(annotated), "\n---\n".join(lines)


# ── tab 2: métricas por clase ──────────────────────────────────────────────────

def plot_per_class():
    csv = EVAL_DIR / "per_class_metrics.csv"
    if not csv.exists():
        return None

    df = pd.read_csv(csv)
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), facecolor="#0f0f0f")
    fig.suptitle("Métricas por clase – HAM10000", color="white", fontsize=14, y=1.01)

    metrics = ["precision", "recall", "f1-score"]
    titles  = ["Precision", "Recall", "F1-score"]
    colours = ["#89b4fa", "#a6e3a1", "#f9e2af"]

    for ax, metric, title, colour in zip(axes, metrics, titles, colours):
        bars = ax.barh(df["class"], df[metric], color=colour, edgecolor="none")
        ax.set_xlim(0, 1)
        ax.set_title(title, color="white", fontsize=12)
        ax.set_facecolor("#1e1e2e")
        ax.tick_params(colors="white")
        ax.spines[:].set_visible(False)
        for bar, val in zip(bars, df[metric]):
            ax.text(val + 0.01, bar.get_y() + bar.get_height() / 2,
                    f"{val:.2f}", va="center", color="white", fontsize=9)

    fig.tight_layout()
    return fig


def get_summary():
    map_file = EVAL_DIR / "map_summary.json"
    report   = EVAL_DIR / "metrics_report.txt"
    if not map_file.exists():
        return "Ejecuta evaluate.py para generar las métricas."
    data = json.loads(map_file.read_text())
    txt  = report.read_text() if report.exists() else ""
    md = (
        f"### Resumen global\n\n"
        f"| Métrica | Valor |\n|---|---|\n"
        f"| **mAP@0.5** | `{data['mAP@0.5']}` |\n"
        f"| **mAP@0.5:0.95** | `{data['mAP@0.5:0.95']}` |\n\n"
        f"```\n{txt}\n```"
    )
    return md


# ── tab 3: curvas de entrenamiento ────────────────────────────────────────────

def plot_training_curves():
    csv = TRAIN_DIR / "results.csv"
    if not csv.exists():
        return None

    df = pd.read_csv(csv, skipinitialspace=True)
    df.columns = df.columns.str.strip()

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor="#0f0f0f")
    fig.suptitle("Curvas de entrenamiento – YOLOv8n", color="white", fontsize=14)

    plots = [
        (axes[0, 0], "train/cls_loss",        "val/cls_loss",        "Classification Loss"),
        (axes[0, 1], "train/box_loss",        "val/box_loss",        "Box Loss"),
        (axes[1, 0], "metrics/mAP50(B)",      None,                  "mAP@0.5"),
        (axes[1, 1], "metrics/mAP50-95(B)",   None,                  "mAP@0.5:0.95"),
    ]

    for ax, train_col, val_col, title in plots:
        ax.set_facecolor("#1e1e2e")
        ax.tick_params(colors="white")
        ax.spines[:].set_color("#313244")
        ax.set_title(title, color="white", fontsize=11)
        ax.set_xlabel("Época", color="#6c7086", fontsize=9)

        if train_col in df.columns:
            ax.plot(df["epoch"], df[train_col], color="#89b4fa",
                    linewidth=2, label="train")
        if val_col and val_col in df.columns:
            ax.plot(df["epoch"], df[val_col], color="#f38ba8",
                    linewidth=2, label="val", linestyle="--")
        ax.legend(facecolor="#313244", labelcolor="white", fontsize=8)

    fig.tight_layout()
    return fig


# ── tab 4: matriz de confusión ────────────────────────────────────────────────

def get_confusion_matrix():
    cm = EVAL_DIR / "confusion_matrix.png"
    if cm.exists():
        return Image.open(cm)
    cm = TRAIN_DIR / "confusion_matrix_normalized.png"
    if cm.exists():
        return Image.open(cm)
    return None


# ── interfaz Gradio ───────────────────────────────────────────────────────────

with gr.Blocks(
    title="Skin Lesion Detector – HAM10000",
    theme=gr.themes.Base(
        primary_hue="blue",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    ),
    css=".gradio-container { max-width: 1100px !important }",
) as demo:

    gr.Markdown(
        "# 🔬 Skin Lesion Detector – HAM10000\n"
        "Modelo **YOLOv8n** entrenado para detectar y clasificar 7 tipos de lesiones cutáneas."
    )

    with gr.Tabs():

        # ── Tab 1 ──────────────────────────────────────────────────────────────
        with gr.Tab("Detección"):
            gr.Markdown("Sube una imagen dermatoscópica y el modelo detectará la lesión y su tipo.")
            with gr.Row():
                with gr.Column():
                    img_input = gr.Image(type="pil", label="Imagen de entrada")
                    btn = gr.Button("Analizar", variant="primary")
                with gr.Column():
                    img_output  = gr.Image(label="Detección")
                    text_output = gr.Markdown(label="Resultado")

            btn.click(fn=run_inference, inputs=img_input,
                      outputs=[img_output, text_output])

            gr.Markdown(
                "**Clases detectables:** "
                + " · ".join(f"`{c}` {CLASS_NAMES[c]}" for c in CLASSES)
            )

        # ── Tab 2 ──────────────────────────────────────────────────────────────
        with gr.Tab("Métricas por clase"):
            gr.Markdown(get_summary())
            plot_output = gr.Plot(label="Precision / Recall / F1 por clase")
            demo.load(fn=plot_per_class, outputs=plot_output)

        # ── Tab 3 ──────────────────────────────────────────────────────────────
        with gr.Tab("Curvas de entrenamiento"):
            curves_output = gr.Plot(label="Loss y mAP durante el entrenamiento")
            demo.load(fn=plot_training_curves, outputs=curves_output)

        # ── Tab 4 ──────────────────────────────────────────────────────────────
        with gr.Tab("Matriz de confusión"):
            cm_output = gr.Image(label="Confusion Matrix")
            demo.load(fn=get_confusion_matrix, outputs=cm_output)


if __name__ == "__main__":
    demo.launch(inbrowser=True)
