from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JARVIS_", env_file=".env", extra="ignore")

    db_path: str = "./data/jarvis.db"
    host: str = "127.0.0.1"
    port: int = 8741
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
