from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARIA_", env_file=".env", extra="ignore")

    db_path: str = "./data/aria.db"
    host: str = "127.0.0.1"
    port: int = 8741
    wake_model: str = "hey_jarvis"   # openwakeword name, or path to a custom .onnx/.tflite
    wake_threshold: float = 0.5
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
