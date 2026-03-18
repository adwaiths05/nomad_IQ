from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_name: str = "Nomadiq API"
    app_env: str = "development"
    app_debug: bool = True
    app_version: str = "0.1.0"
    api_prefix: str = ""

    database_url: str = Field(...)

    jwt_secret_key: str = Field(...)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14

    llm_base_url: str = Field(...)
    llm_model_name: str = Field(...)
    llm_api_key: str | None = None

    embeddings_base_url: str = Field(...)
    embeddings_model_name: str = Field(...)
    embeddings_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
