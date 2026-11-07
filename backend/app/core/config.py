"""Application settings loaded from environment variables / .env."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BACKEND_DIR.parent

# Values that must never be used as a signing key.
_FORBIDDEN_SECRET_MARKERS = ("change", "secret", "default", "example", "placeholder")
_MIN_SECRET_BYTES = 32


class Settings(BaseSettings):
    # Priority: real environment variables (Docker env_file) > backend/.env > root .env.
    # backend/.env holds local overrides for running the API on the host
    # (localhost instead of "db").
    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Runtime connection (app_user) and migration connection (app_owner)
    DATABASE_URL: str
    MIGRATIONS_DATABASE_URL: str

    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = Field(default=15, ge=1, le=60)
    REFRESH_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)

    # Used only by `python -m app.seed`
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""

    MEDIA_DIR: Path = BACKEND_DIR / "media"
    CORS_ORIGINS: Annotated[list[str], NoDecode] = []
    ENABLE_DOCS: bool = False
    TRUST_PROXY: bool = False
    COOKIE_SECURE: bool = True
    DEBUG: bool = False

    @field_validator("JWT_SECRET")
    @classmethod
    def _check_jwt_secret(cls, value: str) -> str:
        value = value.strip()
        if len(value.encode("utf-8")) < _MIN_SECRET_BYTES:
            raise ValueError(
                f"JWT_SECRET must be at least {_MIN_SECRET_BYTES} bytes. "
                "Generate one with: openssl rand -hex 32"
            )
        lowered = value.lower()
        if any(marker in lowered for marker in _FORBIDDEN_SECRET_MARKERS) or len(set(value)) < 8:
            raise ValueError(
                "JWT_SECRET looks like a default or weak value. "
                "Generate one with: openssl rand -hex 32"
            )
        return value

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            value = [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            for origin in value:
                if origin == "*":
                    raise ValueError('CORS_ORIGINS must list exact origins, "*" is not allowed')
                if not origin.startswith(("http://", "https://")):
                    raise ValueError(f"Invalid CORS origin: {origin}")
            value = [origin.rstrip("/") for origin in value]
        return value

    @field_validator("MEDIA_DIR")
    @classmethod
    def _resolve_media_dir(cls, value: Path) -> Path:
        if not value.is_absolute():
            value = BACKEND_DIR / value
        return value.resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
