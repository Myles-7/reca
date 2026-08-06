from __future__ import annotations

from collections.abc import Callable
from functools import cached_property
from pathlib import Path
from typing import Any, Literal, Self, cast

from pydantic import (
    AnyHttpUrl,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvironmentName = Literal["local", "test", "demo", "production"]
ProviderConfigurationStatus = Literal["CONFIGURED", "UNCONFIGURED"]

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_PLACEHOLDER_PREFIXES = ("<replace", "change-me", "changethis", "example-")


def _is_placeholder(value: str) -> bool:
    return value.strip().lower().startswith(_PLACEHOLDER_PREFIXES)


class Settings(BaseSettings):
    """Single, validated configuration entry point for the RECA API.

    Constructing settings only parses local configuration. It does not open any
    database, cache, object-storage, or external-provider connection.
    """

    model_config = SettingsConfigDict(
        env_file=_REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        hide_input_in_errors=True,
        extra="ignore",
    )

    # Application and environment
    PROJECT_NAME: str = "RECA"
    ENVIRONMENT: EnvironmentName = "local"
    API_V1_STR: str = "/api/v1"
    DEMO_MODE: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    MAX_UPLOAD_BYTES: int = Field(default=50_000_000, gt=0)
    EXPORT_MAX_MEMBERS: int = Field(default=5_000, ge=1, le=50_000)
    EXPORT_MAX_ITEM_BYTES: int = Field(default=100_000_000, gt=0)
    EXPORT_MAX_TOTAL_BYTES: int = Field(default=500_000_000, gt=0)
    EXPORT_MAX_PATH_DEPTH: int = Field(default=16, ge=1, le=64)
    EXPORT_MAX_COMPRESSION_RATIO: int = Field(default=100, ge=1, le=10_000)
    CONNECT_TIMEOUT_SECONDS: float = Field(default=5.0, gt=0, le=60)
    REQUEST_TIMEOUT_SECONDS: float = Field(default=30.0, gt=0, le=300)

    # Authentication
    SECRET_KEY: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 8, gt=0)
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: SecretStr

    # PostgreSQL
    POSTGRES_SERVER: str = Field(min_length=1)
    POSTGRES_PORT: int = Field(default=5432, ge=1, le=65535)
    POSTGRES_DB: str = Field(min_length=1)
    POSTGRES_USER: str = Field(min_length=1)
    POSTGRES_PASSWORD: SecretStr

    # Core infrastructure
    VALKEY_URL: str
    MINIO_ENDPOINT: AnyHttpUrl
    MINIO_PUBLIC_ENDPOINT: AnyHttpUrl | None = None
    MINIO_ROOT_USER: str = Field(min_length=3)
    MINIO_ROOT_PASSWORD: SecretStr
    MINIO_BUCKET: str = Field(default="reca", min_length=3)
    GROBID_URL: AnyHttpUrl
    GROBID_PARSE_TIMEOUT_SECONDS: float = Field(default=180.0, gt=0, le=300)
    GROBID_MAX_CONCURRENCY: int = Field(default=2, ge=1, le=8)
    GROBID_MAX_RESPONSE_BYTES: int = Field(default=25_000_000, gt=0)

    # Reserved task infrastructure
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # Optional external providers
    MODEL_BASE_URL: AnyHttpUrl | None = None
    MODEL_API_KEY: SecretStr | None = None
    MODEL_NAME: str | None = None
    OPENALEX_API_URL: AnyHttpUrl = AnyHttpUrl("https://api.openalex.org")
    OPENALEX_API_KEY: SecretStr | None = None
    OPENALEX_CONTACT_EMAIL: EmailStr | None = None
    OPENALEX_CACHE_TTL_SECONDS: int = Field(default=86_400, ge=60, le=604_800)

    # Email, observability, and browser access
    FRONTEND_HOST: AnyHttpUrl = AnyHttpUrl("http://localhost:5173")
    BACKEND_CORS_ORIGINS: list[str] = Field(default_factory=list)
    SENTRY_DSN: AnyHttpUrl | None = None
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = Field(default=587, ge=1, le=65535)
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: SecretStr | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = Field(default=48, gt=0)
    EMAIL_TEST_USER: EmailStr = "test@example.com"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list) and all(isinstance(origin, str) for origin in value):
            return value
        raise ValueError(
            "BACKEND_CORS_ORIGINS must be a comma-separated string or list"
        )

    @field_validator(
        "SENTRY_DSN", "MODEL_BASE_URL", "MINIO_PUBLIC_ENDPOINT", mode="before"
    )
    @classmethod
    def empty_optional_urls_are_none(cls, value: Any) -> Any:
        return None if value == "" else value

    @field_validator(
        "MODEL_API_KEY", "OPENALEX_API_KEY", "SMTP_PASSWORD", mode="before"
    )
    @classmethod
    def empty_optional_secrets_are_none(cls, value: Any) -> Any:
        return None if value == "" else value

    @field_validator("VALKEY_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND")
    @classmethod
    def validate_service_url(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not value.startswith(("valkey://", "redis://", "rediss://")):
            raise ValueError("service URL must use valkey://, redis://, or rediss://")
        return value

    @model_validator(mode="after")
    def validate_environment_security(self) -> Self:
        if self.SMTP_TLS and self.SMTP_SSL:
            raise ValueError("SMTP_TLS and SMTP_SSL cannot both be enabled")

        if self.ENVIRONMENT == "production":
            secret_value = self.SECRET_KEY.get_secret_value()
            if len(secret_value) < 32 or _is_placeholder(secret_value):
                raise ValueError("production SECRET_KEY is invalid")
            if "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError("production CORS cannot use wildcard origins")

        model_fields = (self.MODEL_BASE_URL, self.MODEL_API_KEY, self.MODEL_NAME)
        if any(value is not None for value in model_fields) and not all(
            value is not None for value in model_fields
        ):
            raise ValueError(
                "MODEL_BASE_URL, MODEL_API_KEY, and MODEL_NAME must be configured together"
            )

        return self

    @cached_property
    def all_cors_origins(self) -> list[str]:
        return list(
            dict.fromkeys(
                [*self.BACKEND_CORS_ORIGINS, str(self.FRONTEND_HOST).rstrip("/")]
            )
        )

    @property
    def database_url(self) -> str:
        password = self.POSTGRES_PASSWORD.get_secret_value()
        return (
            "postgresql+psycopg://"
            f"{self.POSTGRES_USER}:{password}@{self.POSTGRES_SERVER}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def secret_key_value(self) -> str:
        return self.SECRET_KEY.get_secret_value()

    @property
    def first_superuser_password_value(self) -> str:
        return self.FIRST_SUPERUSER_PASSWORD.get_secret_value()

    @property
    def smtp_password_value(self) -> str | None:
        return self.SMTP_PASSWORD.get_secret_value() if self.SMTP_PASSWORD else None

    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    @property
    def model_status(self) -> ProviderConfigurationStatus:
        return (
            "CONFIGURED"
            if self.MODEL_BASE_URL and self.MODEL_API_KEY and self.MODEL_NAME
            else "UNCONFIGURED"
        )

    @property
    def openalex_status(self) -> ProviderConfigurationStatus:
        return "CONFIGURED" if self.OPENALEX_API_KEY else "UNCONFIGURED"


# Pydantic Settings resolves required values from the environment at runtime.
settings = cast(Callable[[], Settings], Settings)()
