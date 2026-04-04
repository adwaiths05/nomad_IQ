from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.integrations.background_jobs import refresh_exchange_rates_once, refresh_numbeo_baselines_once
from app.integrations.external_apis import (
    ClimatiqClient,
    ExchangeRateClient,
    GooglePlacesClient,
    GoogleRoutesClient,
    KiwiFlightsClient,
    OpenWeatherClient,
    TicketmasterClient,
    fetch_amadeus_safety_score,
    fetch_numbeo_city_baseline,
)
from app.integrations.mcp_client import FastMCPClient

router = APIRouter(prefix="/integrations", tags=["integrations"])


class RagEnrichRequest(BaseModel):
    context: str
    rag_confidence: float | None = None


class MCPToolRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


class ApifyNewsRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


async def _invoke_mcp_tool(
    server_url: str | None,
    tool_name: str,
    arguments: dict[str, Any],
    timeout_seconds: int = 30,
) -> Any:
    if not server_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MCP server URL is not configured for tool '{tool_name}'",
        )

    data = await FastMCPClient().call_tool(
        server_url=server_url,
        tool_name=tool_name,
        arguments=arguments,
        timeout_seconds=timeout_seconds,
    )
    return data


@router.get("/exchange-rates/{base_currency}")
async def integration_exchange_rates(base_currency: str) -> dict[str, Any]:
    payload = await ExchangeRateClient().get_rates(base_currency)
    return {"base_currency": base_currency.upper(), "data": payload}


@router.get("/google/places/city")
async def integration_google_places_city(city: str, max_results: int = 10) -> dict[str, Any]:
    payload = await GooglePlacesClient().city_productive_spots(city=city, max_results=max_results)
    return {"city": city, "count": len(payload), "items": payload}


@router.get("/google/places/nearby")
async def integration_google_places_nearby(
    latitude: float,
    longitude: float,
    radius_meters: int = 1500,
    max_results: int = 5,
) -> dict[str, Any]:
    payload = await GooglePlacesClient().nearby_productive_spots(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        max_results=max_results,
    )
    return {
        "latitude": latitude,
        "longitude": longitude,
        "count": len(payload),
        "items": payload,
    }


@router.get("/google/routes/transit-duration")
async def integration_google_transit_duration(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
) -> dict[str, Any]:
    minutes = await GoogleRoutesClient().transit_duration_minutes(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        destination_lat=destination_lat,
        destination_lng=destination_lng,
    )
    return {
        "origin": {"lat": origin_lat, "lng": origin_lng},
        "destination": {"lat": destination_lat, "lng": destination_lng},
        "minutes": minutes,
    }


@router.get("/ticketmaster/events")
async def integration_ticketmaster_events(
    city: str,
    start_date: date,
    end_date: date,
    limit: int = 20,
) -> dict[str, Any]:
    payload = await TicketmasterClient().search_events(
        city=city,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return {"city": city, "count": len(payload), "items": payload}


@router.get("/kiwi/flights")
async def integration_kiwi_flights(
    city: str,
    start_date: date | None = None,
    end_date: date | None = None,
    origin_city: str | None = None,
    limit: int = 10,
    currency: str = "USD",
) -> dict[str, Any]:
    payload = await KiwiFlightsClient().search_flights(
        city=city,
        start_date=start_date,
        end_date=end_date,
        origin_city=origin_city,
        limit=limit,
        currency=currency,
    )
    return {"city": city, "origin_city": origin_city, "count": len(payload), "items": payload}


@router.get("/kiwi/nomad")
async def integration_kiwi_nomad(
    origin_city: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    nights_in_dst_from: int | None = None,
    nights_in_dst_to: int | None = None,
    max_fly_duration: int | None = None,
    limit: int = 10,
    currency: str = "USD",
) -> dict[str, Any]:
    payload = await KiwiFlightsClient().search_nomad_deals(
        origin_city=origin_city,
        start_date=start_date,
        end_date=end_date,
        nights_in_dst_from=nights_in_dst_from,
        nights_in_dst_to=nights_in_dst_to,
        max_fly_duration=max_fly_duration,
        limit=limit,
        currency=currency,
    )
    return {"origin_city": origin_city, "data": payload}


@router.get("/openweather/forecast")
async def integration_openweather_forecast(city: str) -> dict[str, Any]:
    payload = await OpenWeatherClient().five_day_forecast(city=city)
    return {"city": city, "data": payload}


@router.get("/climatiq/route-emissions")
async def integration_climatiq_route_emissions(
    distance_km: float,
    mode: str = "passenger_train",
) -> dict[str, Any]:
    payload = await ClimatiqClient().estimate_route_emissions(distance_km=distance_km, mode=mode)
    return {"distance_km": distance_km, "mode": mode, "data": payload}


@router.get("/numbeo/city-baseline")
async def integration_numbeo_city_baseline(city: str) -> dict[str, Any]:
    payload = await fetch_numbeo_city_baseline(city=city)
    return {"city": city, "data": payload}


@router.get("/amadeus/safety-score")
async def integration_amadeus_safety_score(latitude: float, longitude: float) -> dict[str, Any]:
    payload = await fetch_amadeus_safety_score(latitude=latitude, longitude=longitude)
    return {"latitude": latitude, "longitude": longitude, "data": payload}


@router.post("/rag/enrich-context")
async def integration_rag_enrich_context(payload: RagEnrichRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await FastMCPClient().call_tool(
        server_url=settings.mcp_custom_server_url,
        tool_name=settings.mcp_tool_rag_enrich_context,
        arguments={
            "context": payload.context,
            "rag_confidence": payload.rag_confidence,
        },
        timeout_seconds=20,
    )
    return {"data": data}


@router.post("/sync/exchange-rates")
async def integration_sync_exchange_rates() -> dict[str, str]:
    await refresh_exchange_rates_once()
    return {"status": "ok"}


@router.post("/sync/numbeo-baselines")
async def integration_sync_numbeo_baselines() -> dict[str, str]:
    await refresh_numbeo_baselines_once()
    return {"status": "ok"}


@router.post("/google-maps/maps-geocode")
async def integration_google_maps_geocode(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_google_maps_server_url, "maps_geocode", payload.arguments)
    return {"tool": "maps_geocode", "data": data}


@router.post("/google-maps/maps-reverse-geocode")
async def integration_google_maps_reverse_geocode(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_google_maps_server_url, "maps_reverse_geocode", payload.arguments)
    return {"tool": "maps_reverse_geocode", "data": data}


@router.post("/google-maps/maps-search-places")
async def integration_google_maps_search_places(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_google_maps_server_url, "maps_search_places", payload.arguments)
    return {"tool": "maps_search_places", "data": data}


@router.post("/google-maps/maps-place-details")
async def integration_google_maps_place_details(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_google_maps_server_url, "maps_place_details", payload.arguments)
    return {"tool": "maps_place_details", "data": data}


@router.post("/google-maps/maps-distance-matrix")
async def integration_google_maps_distance_matrix(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_google_maps_server_url, "maps_distance_matrix", payload.arguments)
    return {"tool": "maps_distance_matrix", "data": data}


@router.post("/google-maps/maps-elevation")
async def integration_google_maps_elevation(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_google_maps_server_url, "maps_elevation", payload.arguments)
    return {"tool": "maps_elevation", "data": data}


@router.post("/google-maps/maps-directions")
async def integration_google_maps_directions(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_google_maps_server_url, "maps_directions", payload.arguments)
    return {"tool": "maps_directions", "data": data}


@router.post("/openweather/get-five-day-forecast")
async def integration_openweather_get_five_day_forecast(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_openweather_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_five_day_forecast", payload.arguments)
    return {"tool": "get_five_day_forecast", "data": data}


@router.post("/openweather/get-current-weather")
async def integration_openweather_get_current_weather(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_openweather_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_current_weather", payload.arguments)
    return {"tool": "get_current_weather", "data": data}


@router.post("/openweather/get-current-air-pollution")
async def integration_openweather_get_current_air_pollution(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_openweather_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_current_air_pollution", payload.arguments)
    return {"tool": "get_current_air_pollution", "data": data}


@router.post("/openweather/get-air-pollution-forecast")
async def integration_openweather_get_air_pollution_forecast(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_openweather_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_air_pollution_forecast", payload.arguments)
    return {"tool": "get_air_pollution_forecast", "data": data}


@router.post("/openweather/get-direct-geocoding")
async def integration_openweather_get_direct_geocoding(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_openweather_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_direct_geocoding", payload.arguments)
    return {"tool": "get_direct_geocoding", "data": data}


@router.post("/openweather/get-reverse-geocoding")
async def integration_openweather_get_reverse_geocoding(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_openweather_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_reverse_geocoding", payload.arguments)
    return {"tool": "get_reverse_geocoding", "data": data}


@router.post("/ticketmaster/search-events")
async def integration_ticketmaster_search_events(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_ticketmaster_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "search_events", payload.arguments)
    return {"tool": "search_events", "data": data}


@router.post("/ticketmaster/get-event-details")
async def integration_ticketmaster_get_event_details(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_ticketmaster_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_event_details", payload.arguments)
    return {"tool": "get_event_details", "data": data}


@router.post("/ticketmaster/get-event-images")
async def integration_ticketmaster_get_event_images(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_ticketmaster_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_event_images", payload.arguments)
    return {"tool": "get_event_images", "data": data}


@router.post("/ticketmaster/get-classifications")
async def integration_ticketmaster_get_classifications(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_ticketmaster_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_classifications", payload.arguments)
    return {"tool": "get_classifications", "data": data}


@router.post("/ticketmaster/get-segment-details")
async def integration_ticketmaster_get_segment_details(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_ticketmaster_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_segment_details", payload.arguments)
    return {"tool": "get_segment_details", "data": data}


@router.post("/ticketmaster/get-genre-details")
async def integration_ticketmaster_get_genre_details(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_ticketmaster_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_genre_details", payload.arguments)
    return {"tool": "get_genre_details", "data": data}


@router.post("/ticketmaster/get-subgenre-details")
async def integration_ticketmaster_get_subgenre_details(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_ticketmaster_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_subgenre_details", payload.arguments)
    return {"tool": "get_subgenre_details", "data": data}


@router.post("/ticketmaster/get-venues")
async def integration_ticketmaster_get_venues(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_ticketmaster_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_venues", payload.arguments)
    return {"tool": "get_venues", "data": data}


@router.post("/ticketmaster/get-venue-details-enhanced")
async def integration_ticketmaster_get_venue_details_enhanced(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_ticketmaster_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_venue_details_enhanced", payload.arguments)
    return {"tool": "get_venue_details_enhanced", "data": data}


@router.post("/ticketmaster/get-advanced-suggestions")
async def integration_ticketmaster_get_advanced_suggestions(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    server_url = settings.mcp_ticketmaster_server_url or settings.mcp_composio_server_url
    data = await _invoke_mcp_tool(server_url, "get_advanced_suggestions", payload.arguments)
    return {"tool": "get_advanced_suggestions", "data": data}


@router.post("/apify/search-actors")
async def integration_apify_search_actors(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_apify_server_url, "search-actors", payload.arguments)
    return {"tool": "search-actors", "data": data}


@router.post("/apify/fetch-actor-details")
async def integration_apify_fetch_actor_details(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_apify_server_url, "fetch-actor-details", payload.arguments)
    return {"tool": "fetch-actor-details", "data": data}


@router.post("/apify/call-actor")
async def integration_apify_call_actor(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_apify_server_url, "call-actor", payload.arguments, timeout_seconds=60)
    return {"tool": "call-actor", "data": data}


@router.post("/apify/get-actor-run")
async def integration_apify_get_actor_run(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_apify_server_url, "get-actor-run", payload.arguments)
    return {"tool": "get-actor-run", "data": data}


@router.post("/apify/get-actor-output")
async def integration_apify_get_actor_output(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_apify_server_url, "get-actor-output", payload.arguments, timeout_seconds=60)
    return {"tool": "get-actor-output", "data": data}


@router.post("/apify/search-apify-docs")
async def integration_apify_search_apify_docs(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_apify_server_url, "search-apify-docs", payload.arguments)
    return {"tool": "search-apify-docs", "data": data}


@router.post("/apify/fetch-apify-docs")
async def integration_apify_fetch_apify_docs(payload: MCPToolRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await _invoke_mcp_tool(settings.mcp_apify_server_url, "fetch-apify-docs", payload.arguments)
    return {"tool": "fetch-apify-docs", "data": data}


@router.post("/apify/get-latest-news-on-topic")
async def integration_apify_get_latest_news_on_topic(payload: ApifyNewsRequest) -> dict[str, Any]:
    settings = get_settings()
    actor_id = settings.mcp_apify_news_actor_id or "GetLatestNewsOnTopic"
    data = await _invoke_mcp_tool(
        settings.mcp_apify_server_url,
        "call-actor",
        {"actorId": actor_id, "input": payload.input},
        timeout_seconds=60,
    )
    return {"tool": "call-actor", "actor_id": actor_id, "data": data}
