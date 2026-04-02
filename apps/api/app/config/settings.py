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

    mcp_enabled: bool = True
    mcp_auth_token: str | None = None

    # Server URLs for MCP wrappers (FastMCP or compatible HTTP frontends).
    mcp_google_maps_server_url: str | None = None
    mcp_ticketmaster_server_url: str | None = None
    mcp_openweather_server_url: str | None = None
    mcp_composio_server_url: str | None = None
    mcp_custom_server_url: str | None = None
    mcp_apify_server_url: str | None = None

    # Tool mappings for each domain integration.
    # Defaults are aligned to prebuilt MCP servers.
    mcp_tool_google_places_city: str = "maps_search_places"
    mcp_tool_google_places_nearby: str = "maps_search_places"
    mcp_tool_google_routes_transit: str = "maps_distance_matrix"
    mcp_tool_ticketmaster_events: str = "search_events"
    mcp_tool_openweather_forecast: str = "get_five_day_forecast"
    mcp_tool_exchange_rates: str = "exchange_rate_get_rates"
    mcp_tool_numbeo_baseline: str = "numbeo_city_baseline"
    mcp_tool_amadeus_safety: str = "amadeus_safety_score"
    mcp_tool_climatiq_emissions: str = "climatiq_estimate_route_emissions"
    mcp_tool_rag_enrich_context: str = "rag_enrich_plan_context"
    mcp_tool_apify_call_actor: str = "call-actor"
    mcp_tool_apify_get_actor_output: str = "get-actor-output"
    mcp_apify_numbeo_actor_id: str | None = None
    mcp_apify_news_actor_id: str = "GetLatestNewsOnTopic"

    # Optional comma-separated fallback aliases to support provider-specific naming.
    mcp_tool_google_places_city_aliases: str = "maps_search_places,GOOGLE_MAPS_TEXT_SEARCH,google_places_city_productive_spots"
    mcp_tool_google_places_nearby_aliases: str = "maps_search_places,GOOGLE_MAPS_TEXT_SEARCH,google_places_nearby_productive_spots"
    mcp_tool_google_routes_transit_aliases: str = "maps_distance_matrix,maps_directions,GOOGLE_MAPS_DISTANCE_MATRIX_API,google_routes_transit_duration_minutes"
    mcp_tool_ticketmaster_events_aliases: str = "search_events,TICKETMASTER_GET_EVENTS,ticketmaster_search_events"
    mcp_tool_openweather_forecast_aliases: str = "get_five_day_forecast,openweather_five_day_forecast"

@lru_cache
def get_settings() -> Settings:
    return Settings()
