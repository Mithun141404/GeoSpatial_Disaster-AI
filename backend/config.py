"""
DisasterAI Backend - Configuration
Environment variables and settings management
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "DisasterAI Geospatial Intelligence API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_TIMEOUT: int = 120  # seconds
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tiff"]
    UPLOAD_DIR: str = "uploads"
    
    # Geocoding
    GEOCODING_CACHE_TTL: int = 86400  # 24 hours
    GEOCODING_USER_AGENT: str = "DisasterAI/1.0"
    
    # Task Queue (Celery/Redis)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    TASK_TIMEOUT: int = 300  # 5 minutes
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./disasterai.db"
    
    # Caching
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # SMTP for Email Alerts (optional)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = "alerts@disasterai.com"

    # Alert Webhooks
    ALERT_WEBHOOK_URLS: List[str] = []

    # Real-time monitoring settings
    REAL_TIME_MONITORING_ENABLED: bool = True
    ALERT_SUBSCRIPTION_TTL_DAYS: int = 30

    @field_validator("ALERT_WEBHOOK_URLS", mode="before")
    @classmethod
    def parse_webhook_urls(cls, v):
        if isinstance(v, str):
            return [url.strip() for url in v.split(",") if url.strip()]
        return v if v is not None else []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()


# Validation at startup
def validate_settings() -> None:
    """Validate critical settings at startup"""
    if not settings.GEMINI_API_KEY:
        print("⚠️  WARNING: GEMINI_API_KEY not set. The API will use mock responses.")
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
