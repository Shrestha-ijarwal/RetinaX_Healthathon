import os
from pathlib import Path
from typing import Any, List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator, ValidationInfo

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "RetinaX Care"
    API_V1_STR: str = "/api/v1"
    TAGLINE: str = "Closing the Loop in Diabetic Eye Care"
    SUBTITLE: str = "Diabetic Retinopathy Screening Follow-up & Continuity of Care"
    VERSION: str = "2.0.0"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Security
    # In development, a distinct dev-only key is permitted. In production, an external strong key is MANDATORY.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        env = (info.data.get("ENVIRONMENT") or os.getenv("ENVIRONMENT", "development")).lower()
        insecure_placeholders = {
            "",
            "retinax-care-super-secret-key-healthathon-2026-prod-grade",
            "secret",
            "changeme",
            "default_secret",
            "admin",
            "password"
        }
        
        if env == "production":
            if not v or v.strip() in insecure_placeholders or len(v.strip()) < 32:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Production deployment requires a cryptographically "
                    "strong, externally supplied SECRET_KEY (minimum 32 characters). Hardcoded fallback secrets "
                    "are strictly disabled in production mode."
                )
            return v.strip()
        else:
            # Development / local demo fallback
            if not v or v.strip() in insecure_placeholders:
                return "development-only-session-secret-key-for-local-demo-do-not-use-in-production-32c"
            return v.strip()

    # CORS: Explicit allowlist including Vercel live deployment and local dev
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://retina-x01.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return [
            "https://retina-x01.vercel.app",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
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
