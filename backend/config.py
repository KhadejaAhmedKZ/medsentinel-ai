"""Application configuration loaded from environment / .env file."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "MEDSENTINEL AI"
    debug: bool = True
    # Comma-separated list of allowed CORS origins, or "*" for any.
    allowed_origins: str = "*"

    # Gemini (vision + language). Leave the key empty to run fully offline with
    # a deterministic sample scene — the whole demo still works with no network.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
