"""Environment-backed service configuration."""

from functools import lru_cache
from urllib.parse import quote

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings shared by API and worker construction."""

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "deribit"
    postgres_password: str = "deribit"
    postgres_db: str = "deribit"
    redis_host: str = "localhost"
    redis_port: int = 6379
    deribit_base_url: str = "https://www.deribit.com/api/v2"
    deribit_timeout_seconds: float = Field(default=10.0, gt=0)
    deribit_retry_attempts: int = Field(default=3, ge=0)
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        password = quote(self.postgres_password, safe="")
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-by-convention process configuration instance."""
    return Settings()
