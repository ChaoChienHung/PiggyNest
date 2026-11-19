"""Application configuration backed by environment variables and backend/.env."""

from pathlib import Path
import secrets
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"
LOCAL_DATA_DIR = PROJECT_ROOT / "data"


class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "PiggyNest API"
    VERSION: str = "1.0.0"

    # API & CORS
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Paths & Database
    BASE_DIR: Path = PROJECT_ROOT
    DATA_BASE_DIR: str = str(LOCAL_DATA_DIR)
    DATABASE_URL: str = f"sqlite:///{LOCAL_DATA_DIR / 'piggynest.db'}"

    # Security & JWT
    ALGORITHM: str = "HS256"
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Account recovery email (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # Default categories for new users
    DEFAULT_CATEGORIES: List[str] = [
        "Food",
        "Salary",
        "Transport",
        "Entertainment",
        "Others",
    ]

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
