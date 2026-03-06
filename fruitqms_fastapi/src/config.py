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

    # FruitPak Integration
    FRUITPAK_API_URL: Optional[str] = None  # e.g., "https://api.fruitpak.example.com"
    FRUITPAK_API_KEY: Optional[str] = None
    FRUITPAK_TIMEOUT_SECONDS: int = 10

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # File uploads
    MAX_UPLOAD_SIZE_MB: int = 16
    UPLOAD_DIR: str = "./uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
