import os
import tempfile
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


def default_upload_dir() -> Path:
    if os.environ.get("VERCEL") == "1":
        return Path(tempfile.gettempdir()) / "ecowatch-uploads"
    return BASE_DIR / "uploads"


def normalize_database_url(url: str) -> str:
    """Ensure PostgreSQL URLs use the psycopg v3 SQLAlchemy driver."""
    trimmed = url.strip()
    if trimmed.startswith("postgres://"):
        return "postgresql+psycopg://" + trimmed[len("postgres://") :]
    if trimmed.startswith("postgresql://"):
        return "postgresql+psycopg://" + trimmed[len("postgresql://") :]
    return trimmed


class Settings(BaseSettings):
    PROJECT_NAME: str = "Community Waste Reporting System"
    API_V1_PREFIX: str = "/api"
    SECRET_KEY: str = "cwrs-dev-secret-key-change-in-production-9f8e7d6c5b4a"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # PostgreSQL primary database (override in backend/.env)
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/waste_report_db"

    # Cloudinary file storage configuration
    STORAGE_BACKEND: str = "cloudinary"  # "cloudinary" | "s3_compatible" | "local"
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_URL: str = ""
    CLOUDINARY_FOLDER: str = "waste_reports"

    # S3-Compatible Object Storage (Sabay Cloud S3, AWS S3, Cloudflare R2, MinIO)
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = "us-east-1"
    S3_BUCKET: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_PUBLIC_BASE_URL: str = ""
    S3_FOLDER: str = "waste_reports"

    # Upload security constraints
    UPLOAD_DIR: Path = default_upload_dir()
    ALLOWED_EXTENSIONS: set[str] = {"png", "jpg", "jpeg", "webp"}
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "https://waste-report-system-frontend.vercel.app",
        "https://www.wastereport.website",
    ]

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_db_url(cls, value: str) -> str:
        return normalize_database_url(value)

    @property
    def cloudinary_configured(self) -> bool:
        return bool(
            self.CLOUDINARY_URL
            or (self.CLOUDINARY_CLOUD_NAME and self.CLOUDINARY_API_KEY and self.CLOUDINARY_API_SECRET)
        )


settings = Settings()
