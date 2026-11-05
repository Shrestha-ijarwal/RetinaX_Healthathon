import os
from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "RetinaX Care"
    API_V1_STR: str = "/api/v1"
    TAGLINE: str = "Closing the Loop in Diabetic Eye Care"
    SUBTITLE: str = "Diabetic Retinopathy Screening Follow-up & Continuity of Care"
    VERSION: str = "2.0.0"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "retinax-care-super-secret-key-healthathon-2026-prod-grade")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
    ]

    # Database: Supports PostgreSQL or local SQLite fallback
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{ROOT_DIR / 'data' / 'retinax_care.db'}"
    )

    # Redis & Background Tasks
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    # Storage (Local or S3/MinIO)
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")  # "local" or "s3"
    STORAGE_DIR: Path = ROOT_DIR / "uploads"
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-south-1")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "retinax-care-documents")
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "")  # For MinIO

    # Document upload limits and validation
    MAX_UPLOAD_SIZE_BYTES: int = 32 * 1024 * 1024  # 32 MB
    ALLOWED_EXTENSIONS: set = {"pdf", "jpg", "jpeg", "png"}
    ALLOWED_MIME_TYPES: set = {
        "application/pdf",
        "image/jpeg",
        "image/png"
    }

    # Scope and Legal Disclaimer
    DISCLAIMER: str = (
        "RetinaX Care supports operational care coordination and continuity tracking. "
        "It does not provide diagnosis, clinical risk assessment, treatment recommendations, "
        "or autonomous clinical decision-making. Clinical decisions remain the responsibility "
        "of qualified healthcare professionals."
    )

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
