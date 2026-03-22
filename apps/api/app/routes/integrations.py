from datetime import date
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.config.settings import get_settings
from app.integrations.background_jobs import refresh_exchange_rates_once, refresh_numbeo_baselines_once
from app.integrations.external_apis import (
    ClimatiqClient,
    ExchangeRateClient,
    GooglePlacesClient,
    GoogleRoutesClient,
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
