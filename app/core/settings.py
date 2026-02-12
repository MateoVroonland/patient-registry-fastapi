from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/prueba"
    uploads_dir: Path = Field(default=Path("data/uploads"))
    file_chunk_size: int = 1024 * 1024

    mail_host: str | None = None
    mail_port: int | None = None
    mail_username: str | None = None
    mail_password: str | None = None
    mail_from_email: str | None = None
    mail_from_name: str | None = None


settings = Settings()
