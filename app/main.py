"""
Desktop application for HAM10000 skin lesion detection.

Features:
  - Load an image from disk
  - Run YOLO inference and overlay detection boxes
  - Show per-class confidence scores
  - Display training metrics (mAP, confusion matrix) from results/eval/

Run:
    python app/main.py
"""

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk

BASE_DIR   = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "best.pt"
EVAL_DIR   = BASE_DIR / "results" / "eval"

CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
CLASS_LABELS = {
    "akiec": "Actinic Keratosis",
    "bcc":   "Basal Cell Carcinoma",
    "bkl":   "Benign Keratosis",
    "df":    "Dermatofibroma",
    "mel":   "Melanoma",
    "nv":    "Melanocytic Nevus",
    "vasc":  "Vascular Lesion",
}
# one distinct colour per class (BGR → RGB for PIL)
COLOURS = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8",
    "#f58231", "#911eb4", "#42d4f4",
]

DISPLAY_W = 600
DISPLAY_H = 450


def load_model():
    if not MODEL_PATH.exists():
        return None
    from ultralytics import YOLO
    return YOLO(str(MODEL_PATH))


def draw_detections(pil_img: Image.Image, boxes, names) -> Image.Image:
    draw = ImageDraw.Draw(pil_img)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()

    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        cls  = int(box.cls[0])
        conf = float(box.conf[0])
        colour = COLOURS[cls % len(COLOURS)]
        draw.rectangle([x1, y1, x2, y2], outline=colour, width=3)
        label = f"{CLASSES[cls]} {conf:.0%}"
        draw.rectangle([x1, y1 - 20, x1 + len(label) * 9, y1], fill=colour)
        draw.text((x1 + 2, y1 - 18), label, fill="white", font=font)
    return pil_img


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Skin Lesion Detector – HAM10000")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")

        self.model   = None
        self.current_image_path = None
        self._build_ui()
        self._load_model_async()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── top bar ──
        top = tk.Frame(self, bg="#313244", pady=6)
        top.pack(fill="x")

        tk.Label(top, text="Skin Lesion Detector", font=("Helvetica", 16, "bold"),
                 fg="#cdd6f4", bg="#313244").pack(side="left", padx=12)

        self.model_status = tk.Label(top, text="⏳ Loading model…",
                                     font=("Helvetica", 10), fg="#fab387", bg="#313244")
        self.model_status.pack(side="right", padx=12)

        # ── main area ──
        main = tk.Frame(self, bg="#1e1e2e")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # left: image canvas
        left = tk.Frame(main, bg="#1e1e2e")
        left.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Label(left, bg="#181825",
                               width=DISPLAY_W, height=DISPLAY_H,
                               text="No image loaded\n\nClick 'Open Image' to start",
                               fg="#6c7086", font=("Helvetica", 12))
        self.canvas.pack()

        btn_frame = tk.Frame(left, bg="#1e1e2e", pady=6)
        btn_frame.pack()

        self._btn("Open Image",  self._open_image,  btn_frame, "#89b4fa").pack(side="left", padx=4)
        self._btn("Run Detection", self._run_detect, btn_frame, "#a6e3a1").pack(side="left", padx=4)
        self._btn("View Metrics", self._show_metrics, btn_frame, "#f9e2af").pack(side="left", padx=4)

        # right: results panel
        right = tk.Frame(main, bg="#181825", width=260, padx=10, pady=10)
        right.pack(side="right", fill="y", padx=(8, 0))
        right.pack_propagate(False)

        tk.Label(right, text="Detections", font=("Helvetica", 12, "bold"),
                 fg="#cdd6f4", bg="#181825").pack(anchor="w")

        self.result_text = tk.Text(right, bg="#181825", fg="#cdd6f4",
                                   font=("Consolas", 10), state="disabled",
                                   relief="flat", wrap="word", height=20)
        self.result_text.pack(fill="both", expand=True, pady=(4, 0))

    @staticmethod
    def _btn(text, cmd, parent, colour):
        return tk.Button(parent, text=text, command=cmd,
                         bg=colour, fg="#1e1e2e", font=("Helvetica", 10, "bold"),
                         relief="flat", padx=10, pady=4, cursor="hand2",
                         activebackground=colour)

    # ── model loading ─────────────────────────────────────────────────────────

    def _load_model_async(self):
        self.after(100, self._load_model)

    def _load_model(self):
        self.model = load_model()
        if self.model:
            self.model_status.config(text="✓ Model loaded", fg="#a6e3a1")
        else:
            self.model_status.config(text="✗ Model not found – train first", fg="#f38ba8")

    # ── image handling ────────────────────────────────────────────────────────

    def _open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not path:
            return
        self.current_image_path = Path(path)
        img = Image.open(path).convert("RGB")
        self._show_pil(img)
        self._set_results("Image loaded.\nClick 'Run Detection' to analyse.")

    def _show_pil(self, pil_img: Image.Image):
        pil_img = pil_img.copy()
        pil_img.thumbnail((DISPLAY_W, DISPLAY_H), Image.LANCZOS)
        self._tk_img = ImageTk.PhotoImage(pil_img)
        self.canvas.config(image=self._tk_img, text="")

    # ── detection ─────────────────────────────────────────────────────────────

    def _run_detect(self):
        if not self.current_image_path:
            messagebox.showinfo("No image", "Please open an image first.")
            return
        if not self.model:
            messagebox.showerror("No model", "Model not loaded. Run train.py first.")
            return

        results = self.model(str(self.current_image_path), verbose=False)[0]
        img = Image.open(self.current_image_path).convert("RGB")

        lines = []
        if results.boxes and len(results.boxes):
            img = draw_detections(img, results.boxes, results.names)
            for box in results.boxes:
                cls  = int(box.cls[0])
                conf = float(box.conf[0])
                name = CLASSES[cls]
                full = CLASS_LABELS.get(name, name)
                lines.append(f"• {full}\n  confidence: {conf:.1%}\n")
        else:
            lines.append("No lesions detected.")

        self._show_pil(img)
        self._set_results("\n".join(lines))

    # ── metrics window ────────────────────────────────────────────────────────

    def _show_metrics(self):
        map_file = EVAL_DIR / "map_summary.json"
        csv_file  = EVAL_DIR / "per_class_metrics.csv"
        cm_file   = EVAL_DIR / "confusion_matrix.png"

        win = tk.Toplevel(self)
        win.title("Model Metrics")
        win.configure(bg="#1e1e2e")

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        # ── tab 1: summary ──
        t1 = tk.Frame(nb, bg="#1e1e2e")
        nb.add(t1, text="Summary")

        if map_file.exists():
            data = json.loads(map_file.read_text())
            for k, v in data.items():
                row = tk.Frame(t1, bg="#1e1e2e")
                row.pack(anchor="w", padx=16, pady=4)
                tk.Label(row, text=f"{k}:", width=18, anchor="w",
                         fg="#89b4fa", bg="#1e1e2e", font=("Consolas", 11)).pack(side="left")
                tk.Label(row, text=str(v), fg="#cdd6f4", bg="#1e1e2e",
                         font=("Consolas", 11, "bold")).pack(side="left")
        else:
            tk.Label(t1, text="Run evaluate.py to generate metrics.",
                     fg="#f38ba8", bg="#1e1e2e", font=("Helvetica", 11)).pack(pady=20)

        # ── tab 2: per-class table ──
        t2 = tk.Frame(nb, bg="#1e1e2e")
        nb.add(t2, text="Per-class")

        if csv_file.exists():
            import pandas as pd
            df = pd.read_csv(csv_file)
            cols = list(df.columns)
            tree = ttk.Treeview(t2, columns=cols, show="headings", height=len(df))
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=90, anchor="center")
            for _, r in df.iterrows():
                tree.insert("", "end", values=list(r))
            tree.pack(padx=10, pady=10)
        else:
            tk.Label(t2, text="Run evaluate.py first.",
                     fg="#f38ba8", bg="#1e1e2e", font=("Helvetica", 11)).pack(pady=20)

        # ── tab 3: confusion matrix ──
        t3 = tk.Frame(nb, bg="#1e1e2e")
        nb.add(t3, text="Confusion Matrix")

        if cm_file.exists():
            cm_img = Image.open(cm_file)
            cm_img.thumbnail((700, 550), Image.LANCZOS)
            self._cm_tk = ImageTk.PhotoImage(cm_img)
            tk.Label(t3, image=self._cm_tk, bg="#1e1e2e").pack(padx=8, pady=8)
        else:
            tk.Label(t3, text="Run evaluate.py to generate the confusion matrix.",
                     fg="#f38ba8", bg="#1e1e2e", font=("Helvetica", 11)).pack(pady=20)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _set_results(self, text: str):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", text)
        self.result_text.config(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
