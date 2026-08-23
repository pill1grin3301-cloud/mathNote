from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    telegram_token: str | None = None
    admin_telegram_chat_id: int | None = None
    telegram_proxy: str | None = None
    cors_allowed_origins: str = (
        "http://localhost:8767,http://127.0.0.1:8767,"
        "http://localhost:8080,http://127.0.0.1:8080,"
        "http://localhost:8042,http://127.0.0.1:8042"
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @field_validator("telegram_token", "telegram_proxy", mode="before")
    @classmethod
    def strip_optional_str(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )


settings = Settings()
