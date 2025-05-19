# core/config.py
from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging


class Settings(BaseSettings):
    # единый источник настроек
    model_config = SettingsConfigDict(
        env_prefix="GADGETBRIDGE_",   # <-- всё начинается с этого префикса
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # поля
    db_path: Path
    api_key: str | None = None
    min_my_weight: float = 60
    max_my_weight: float = 150
    rate_limit: int = 60
    log_level: str = "INFO"

    @model_validator(mode="after")
    def validate_settings(self):
        errors = []
        if self.min_my_weight >= self.max_my_weight:
            errors.append("min_my_weight должен быть меньше max_my_weight")
        if not self.db_path or not self.db_path.exists():
            errors.append(f"Файл базы данных не найден: {self.db_path}")
        if errors:
            for err in errors:
                logging.error(f"[Settings validation] {err}")
            raise ValueError("; ".join(errors))
        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()
