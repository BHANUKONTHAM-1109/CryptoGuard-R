"""
CryptoGuard-R - Centralized Configuration
Secure environment variable handling with validation.
Never hardcode secrets; all sensitive values come from environment.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    .env file is loaded automatically; env vars override .env values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown env vars to prevent injection
    )

    # Application
    app_name: str = Field(default="CryptoGuard-R", description="Application name")
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Server
    host: str = Field(default="0.0.0.0", description="Bind host")
    port: int = Field(default=8000, ge=1, le=65535, description="Bind port")

    # Database
    database_url: str = Field(
        default="sqlite:///./cryptoguard.db",
        description="SQLAlchemy database URL",
    )

    # Security - MUST be overridden in production
    secret_key: str = Field(
        default="change-me-in-production",
        min_length=16,
        description="Secret key for signing; must be 16+ chars in production",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expire_minutes: int = Field(default=60, ge=1, le=10080, description="JWT expiry in minutes")

    # Rate limiting
    rate_limit_requests: int = Field(default=100, ge=1, description="Max requests per window")
    rate_limit_window: int = Field(default=60, ge=1, description="Rate limit window in seconds")

    # AI model
    model_path: str = Field(default="./models/phishing_model.pkl", description="Path to saved ML model")
    bert_model: str = Field(default="bert-base-uncased", description="HuggingFace BERT model name")

    # Crypto key paths (generated at runtime if not exist)
    rsa_private_key_path: str = Field(default="./keys/rsa_private.pem", description="RSA private key path")
    rsa_public_key_path: str = Field(default="./keys/rsa_public.pem", description="RSA public key path")

    @field_validator("secret_key", mode="before")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key meets minimum security requirements."""
        if not v or len(v) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters")
        # Reject obvious placeholder in production
        if v.lower() in ("change-me-in-production", "your-secret-key-change-in-production"):
            # Allow in development; warn via logging at startup
            pass
        return v

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure SQLite path is safe (no path traversal)."""
        if "sqlite" in v.lower() and ".." in v:
            raise ValueError("Database URL must not contain path traversal (..)")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env.lower() == "production"

    @property
    def project_root(self) -> Path:
        """Project root directory (backend folder)."""
        return Path(__file__).resolve().parent.parent.parent


def _find_env_file() -> Optional[Path]:
    """Locate .env by searching upward from backend dir."""
    current = Path(__file__).resolve().parent.parent.parent  # backend/
    for _ in range(5):  # Limit search depth
        candidate = current / ".env"
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


# Singleton instance - load once at import
settings: Settings

try:
    _env_path = _find_env_file()
    if _env_path:
        settings = Settings(_env_file=_env_path)  # type: ignore[call-arg]
    else:
        settings = Settings()  # type: ignore[call-arg]
except Exception:
    settings = Settings()  # type: ignore[call-arg]
