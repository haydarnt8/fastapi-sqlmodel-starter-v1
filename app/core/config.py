"""
Application Configuration using Pydantic Settings

This module provides type-safe configuration management with:
- Environment variable validation
- Type conversion
- Default values
- Multiple environment support (dev/staging/prod)

Why Pydantic Settings?
- Type safety: Catches config errors at startup
- Validation: Ensures all required configs are present
- IDE support: Autocomplete for config values
- Documentation: Self-documenting configuration
"""

from typing import List, Optional
from pydantic import field_validator, EmailStr, PostgresDsn, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Usage:
        from app.core.config import get_settings
        settings = get_settings()
        print(settings.DATABASE_URL)
    """

    # Application
    APP_NAME: str = "FastAPI Starter"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "Production-grade FastAPI Application Starter Template"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True  # Auto-reload on code changes (dev only)

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    DB_ECHO: bool = False  # Log SQL queries (useful for debugging)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Convert Render PostgreSQL URL format to SQLAlchemy async format.

        Render provides: postgres://user:pass@host:port/db
        We need: postgresql+asyncpg://user:pass@host:port/db
        """
        if v.startswith("postgres://"):
            # Render uses postgres:// but we need postgresql+asyncpg://
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            # Some providers use postgresql:// - convert to async
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Security
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-USE-CRYPTOGRAPHICALLY-SECURE-KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        """
        Validate SECRET_KEY security in production.

        In production, SECRET_KEY must be:
        - Changed from default
        - At least 32 characters long
        - Cryptographically secure
        """
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production":
            if "CHANGE-ME" in v or len(v) < 32:
                raise ValueError(
                    "SECRET_KEY must be changed from default and be at least 32 characters in production. "
                    "Generate a secure key with: openssl rand -hex 32"
                )
        return v

    # Password hashing
    PWD_SCHEMES: List[str] = ["bcrypt"]
    PWD_DEPRECATED: str = "auto"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",  # Vite default
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """
        Parse CORS origins from string or list.
        Supports: "http://localhost:3000,http://localhost:8000"
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_ENABLED: bool = True

    # Redis (for caching and token revocation)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_ENABLED: bool = True  # Graceful fallback if Redis not available

    # Admin User (created on first startup)
    FIRST_SUPERUSER_EMAIL: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "changeme123"
    FIRST_SUPERUSER_FULLNAME: str = "System Administrator"

    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: Optional[str] = None  # Log file path (None = stdout only)

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Starter"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Email (for future password reset, notifications)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "application/pdf"]

    # Monitoring & Performance
    ENABLE_METRICS: bool = False
    ENABLE_PROFILING: bool = False
    REQUEST_TIMEOUT: int = 30  # seconds

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",  # Allow extra fields in .env
    )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for Alembic migrations)."""
        url = self.DATABASE_URL
        # Remove async drivers
        url = url.replace("+aiosqlite", "")
        url = url.replace("+asyncpg", "")
        # Ensure postgresql uses psycopg2 (sync driver)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get settings singleton instance.

    This ensures settings are loaded only once and reused throughout the app.

    Returns:
        Settings: Application settings instance

    Example:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"Running in {settings.ENVIRONMENT} mode")
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience export
settings = get_settings()
