"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """All settings loaded from environment variables or .env file."""

    # Application
    APP_NAME: str = "FruitQMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database — defaults to async SQLite for local dev, use PostgreSQL in production
    DATABASE_URL: str = "sqlite+aiosqlite:///./fruitqms.db"

    # JWT Authentication
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # FruitPak Integration (JWT auth — no API keys yet)
    FRUITPAK_API_URL: Optional[str] = None  # e.g., "http://localhost:3000" or "https://api.fruitpak.com"
    FRUITPAK_EMAIL: Optional[str] = None  # dedicated QMS service user in FruitPak
    FRUITPAK_PASSWORD: Optional[str] = None
    FRUITPAK_TIMEOUT_SECONDS: int = 10
    FRUITPAK_POLL_INTERVAL_MINUTES: int = 10  # how often to poll for new batches

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # File uploads
    MAX_UPLOAD_SIZE_MB: int = 16
    UPLOAD_DIR: str = "./uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
