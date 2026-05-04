from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Email Marketing Platform"
    debug: bool = False
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/email_marketing"
    sync_database_url: str = "postgresql://postgres:postgres@localhost:5432/email_marketing"

    redis_url: str = "redis://localhost:6379/0"

    # Fernet key (url-safe base64 32 bytes) — generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
    encryption_key: str = ""

    api_rate_limit: str = "100/minute"

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    email_campaign_queue: str = "email_campaign_queue"


@lru_cache
def get_settings() -> Settings:
    return Settings()
