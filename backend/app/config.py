import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения."""

    database_url: str
    app_port: int = 8000
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:8000"
    carbs_per_bread_unit: float = 12.0
    app_timezone: str = "Europe/Moscow"

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    model_config = SettingsConfigDict(
        env_file=os.path.join(Path(__file__).parent.parent.parent, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()