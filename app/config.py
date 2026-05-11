from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["dev", "test", "prod"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        frozen=True,
    )

    env: Environment = "dev"
    log_level: LogLevel = "INFO"

    database_url: PostgresDsn = PostgresDsn("postgresql+asyncpg://mneme:mneme@localhost:5432/mneme")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
