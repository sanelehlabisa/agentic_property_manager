from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str | None = None
    frontend_origin: str | None = None

    protocol: str = "http"
    host: str = "localhost"
    frontend_port: int = 5173
    postgres_db: str | None = None
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_host: str | None = None

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def derive_service_urls(self) -> "Settings":
        if self.frontend_origin is None:
            self.frontend_origin = f"{self.protocol}://{self.host}:{self.frontend_port}"

        if self.database_url is None:
            database_parts = {
                "POSTGRES_DB": self.postgres_db,
                "POSTGRES_USER": self.postgres_user,
                "POSTGRES_PASSWORD": self.postgres_password,
                "POSTGRES_HOST": self.postgres_host,
            }
            missing = [name for name, value in database_parts.items() if not value]
            if missing:
                names = ", ".join(missing)
                raise ValueError(f"Missing database configuration: {names}")

            password = quote_plus(self.postgres_password)
            self.database_url = (
                f"postgresql+psycopg://{self.postgres_user}:{password}"
                f"@{self.postgres_host}:5432/{self.postgres_db}"
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
