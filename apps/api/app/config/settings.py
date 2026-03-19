from functools import lru_cache
import importlib
from pydantic import Field

_pydantic_settings = importlib.util.find_spec("pydantic_settings")
if _pydantic_settings is not None:
    _settings_module = importlib.import_module("pydantic_settings")
    BaseSettings = _settings_module.BaseSettings
    SettingsConfigDict = _settings_module.SettingsConfigDict
else:
    from pydantic.v1 import BaseSettings

    class SettingsConfigDict(dict):
        pass


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

    redis_url: str = "redis://redis:6379/0"

    exchange_rate_api_key: str | None = None
    exchange_rate_base_url: str = "https://v6.exchangerate-api.com/v6"

    google_places_api_key: str | None = None
    google_places_base_url: str = "https://maps.googleapis.com/maps/api/place"

    google_routes_api_key: str | None = None
    google_routes_base_url: str = "https://routes.googleapis.com"

    openweather_api_key: str | None = None
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"

    ticketmaster_api_key: str | None = None
    ticketmaster_base_url: str = "https://app.ticketmaster.com/discovery/v2"

    amadeus_api_key: str | None = None
    amadeus_api_secret: str | None = None
    amadeus_base_url: str = "https://test.api.amadeus.com"

    climatiq_api_key: str | None = None
    climatiq_base_url: str = "https://api.climatiq.io"

    apify_api_token: str | None = None
    apify_base_url: str = "https://api.apify.com/v2"
    numbeo_apify_actor_id: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
