from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Skin Lesion Detector API"
    app_version: str = "0.1.0"

    model_path: Path = Path(__file__).resolve().parents[2] / "models" / "best.pt"

    # Inference
    conf_threshold: float = 0.25
    iou_threshold: float = 0.45

    class Config:
        env_file = ".env"


settings = Settings()
