from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    db_path: str = Field(..., env="DB_PATH")
    api_key: str | None = Field(None, env="API_KEY")
    min_my_weight: float = Field(60, env="MIN_MY_WEIGHT")
    max_my_weight: float = Field(150, env="MAX_MY_WEIGHT")
    rate_limit: int = Field(60, env="RATE_LIMIT")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()