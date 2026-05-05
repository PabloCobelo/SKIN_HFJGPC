import io
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from app.core.config import settings
from app.core.model import ModelManager
from app.schemas.prediction import CLASSES, CLASS_NAMES, BoundingBox, Detection, PredictionResponse

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    contents = await file.read()
    pil_img = Image.open(io.BytesIO(contents)).convert("RGB")
    img_np = np.array(pil_img)

    model = ModelManager.get()
    results = model(
        img_np,
        conf=settings.conf_threshold,
        iou=settings.iou_threshold,
        verbose=False,
    )[0]

    detections: list[Detection] = []
    if results.boxes and len(results.boxes):
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cls_id = int(box.cls[0])
            conf   = float(box.conf[0])
            code   = CLASSES[cls_id]
            detections.append(Detection(
                class_id=cls_id,
                class_code=code,
                class_name=CLASS_NAMES[code],
                confidence=round(conf, 4),
                bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
            ))

    h, w = img_np.shape[:2]
    return PredictionResponse(detections=detections, image_width=w, image_height=h)
