from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


def to_async_database_url(url: str) -> tuple[str, dict]:
    """Normalize DB URL for async SQLAlchemy. Returns (url, connect_args)."""
    connect_args: dict = {}

    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    elif url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgres://")

    if not url.startswith("postgresql+asyncpg://"):
        return url, connect_args

    # libpq query params aren't valid asyncpg connect() kwargs — peel them off.
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    if sslmode in {"require", "verify-ca", "verify-full", "prefer"}:
        connect_args["ssl"] = True
    url = urlunparse(parsed._replace(query=urlencode(query)))
    return url, connect_args


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "travelPanda"
    debug: bool = False
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite+aiosqlite:///./travelpanda.db"
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None

    @property
    def async_database_url(self) -> str:
        return to_async_database_url(self.database_url)[0]

    @property
    def database_connect_args(self) -> dict:
        return to_async_database_url(self.database_url)[1]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
