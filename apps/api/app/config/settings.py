from functools import lru_cache
import importlib

from pydantic import Field

_pydantic_settings = importlib.util.find_spec("pydantic_settings")


class _SettingsFields:
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

    mcp_enabled: bool = True
    mcp_auth_token: str | None = None

    mcp_travel_url: str = "http://mcp-travel:9000"
    mcp_rag_url: str = "http://mcp-rag:9000"

    mcp_tool_travel_search_flights: str = "search_flights"
    mcp_tool_travel_search_nomad_deals: str = "search_nomad_deals"
    mcp_tool_travel_city_spots: str = "get_city_spots"
    mcp_tool_travel_nearby_spots: str = "get_nearby_spots"
    mcp_tool_travel_transit_duration: str = "calculate_transit_duration"

    mcp_tool_rag_search_long_term: str = "search_long_term_memory"
    mcp_tool_rag_search_short_term: str = "search_short_term_memory"
    mcp_tool_rag_store: str = "store_memory"

    travelpayouts_api_token: str | None = None
    travelpayouts_base_url: str = "https://api.travelpayouts.com/v1"

    openweather_api_key: str | None = None
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    openweather_geo_base_url: str = "https://api.openweathermap.org/geo/1.0"
    openweather_onecall_base_url: str = "https://api.openweathermap.org/data/3.0"

    ticketmaster_api_key: str | None = None
    ticketmaster_base_url: str = "https://app.ticketmaster.com/discovery/v2"
    eventbrite_api_token: str | None = None
    eventbrite_base_url: str = "https://www.eventbriteapi.com/v3"

    exchange_api_base_url: str = "https://open.er-api.com/v6"
    apify_api_token: str | None = None
    numbeo_city_cost_actor_id: str | None = None

    climatiq_api_key: str | None = None
    climatiq_base_url: str = "https://api.climatiq.io"

    safety_secondary_signal_enabled: bool = True

if _pydantic_settings is not None:
    _settings_module = importlib.import_module("pydantic_settings")

    class Settings(_SettingsFields, _settings_module.BaseSettings):
        model_config = _settings_module.SettingsConfigDict(env_file=None, extra="ignore")

else:
    from pydantic.v1 import BaseSettings

    class Settings(_SettingsFields, BaseSettings):
        class Config:
            env_file = None
            extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
