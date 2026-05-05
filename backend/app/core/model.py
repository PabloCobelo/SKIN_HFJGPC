from pathlib import Path
from ultralytics import YOLO
from .config import settings


class ModelManager:
    _instance: YOLO | None = None

    @classmethod
    def get(cls) -> YOLO:
        if cls._instance is None:
            if not settings.model_path.exists():
                raise FileNotFoundError(
                    f"Model not found at {settings.model_path}. "
                    "Run ml/scripts/train.py first."
                )
            cls._instance = YOLO(str(settings.model_path))
        return cls._instance
