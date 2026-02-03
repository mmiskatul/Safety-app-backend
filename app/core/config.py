from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # FastAPI
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Safety App API"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_DATABASE_URL: Optional[str] = None
    
    # YOLO
    YOLO_MODEL_PATH: str = "yolov11_models/safety_ppe_model.pt"
    YOLO_CONFIG_PATH: str = "yolov11_models/config.yaml"
    
    # Detection Settings
    CONFIDENCE_THRESHOLD: float = 0.5
    DETECTION_CLASSES: list = [
        "helmet", "gloves", "vest", "glasses", 
        "harness", "machinery_proximity", 
        "fall_risk", "phone_usage", "low_visibility"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()