from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LocalOpsBot"
    environment: str = "local"

    redis_host: str = "redis"
    redis_port: int = 6379

    database_path: str = "/app/data/localopsbot.db"

    max_retries: int = 3
    retry_base_delay: float = 1
    retry_max_delay: float = 10

    llm_timeout_seconds: float = 3
    max_processing_time_seconds: float = 30

    shutdown_timeout_seconds: int = 20

    failure_mode: str = "success"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()