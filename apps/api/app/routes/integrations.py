from datetime import date
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.integrations.external_apis import (
    ClimatiqClient,
    ExchangeRateClient,
    MapsClient,
    MapsRoutesClient,
    OpenWeatherClient,
    TicketmasterClient,
    TransportClient,
    fetch_amadeus_safety_score,
    fetch_numbeo_city_baseline,
)
from app.integrations.mcp_client import FastMCPClient
from app.config.settings import get_settings

router = APIRouter(prefix="/integrations", tags=["integrations"])


class TransportFlightsRequest(BaseModel):
    city: str
    start_date: date | None = None
    end_date: date | None = None
    origin_city: str | None = None
    limit: int = 10
    currency: str = "USD"


class TransportNomadRequest(BaseModel):
    origin_city: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    nights_in_dst_from: int | None = None
    nights_in_dst_to: int | None = None
    max_fly_duration: int | None = None
    limit: int = 10
    currency: str = "USD"


class MapsCityRequest(BaseModel):
    city: str
    max_results: int = 10


class MapsNearbyRequest(BaseModel):
    latitude: float
    longitude: float
    radius_meters: int = 1500
    max_results: int = 5


class MapsTransitRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float


class EventsSearchRequest(BaseModel):
    city: str
    start_date: date
    end_date: date
    limit: int = 20


class WeatherForecastRequest(BaseModel):
    city: str


class FinanceExchangeRequest(BaseModel):
    base_currency: str = "USD"


class FinanceBaselineRequest(BaseModel):
    city: str


class SafetyScoreRequest(BaseModel):
    latitude: float
    longitude: float


class WellnessSignalsRequest(BaseModel):
    city: str


class EnvironmentRouteRequest(BaseModel):
    distance_km: float
    mode: str = "passenger_train"


class RagSearchRequest(BaseModel):
    query: str
    limit: int = 5


class RagStoreRequest(BaseModel):
    content: str
    memory_type: str = "short_term"
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/transport/search-flights")
async def transport_search_flights(payload: TransportFlightsRequest) -> dict[str, Any]:
    data = await TransportClient().search_flights(
        city=payload.city,
        start_date=payload.start_date,
        end_date=payload.end_date,
        origin_city=payload.origin_city,
        limit=payload.limit,
        currency=payload.currency,
    )
    return {"items": data, "count": len(data)}


@router.post("/transport/search-nomad-deals")
async def transport_search_nomad_deals(payload: TransportNomadRequest) -> dict[str, Any]:
    data = await TransportClient().search_nomad_deals(
        origin_city=payload.origin_city,
        start_date=payload.start_date,
        end_date=payload.end_date,
        nights_in_dst_from=payload.nights_in_dst_from,
        nights_in_dst_to=payload.nights_in_dst_to,
        max_fly_duration=payload.max_fly_duration,
        limit=payload.limit,
        currency=payload.currency,
    )
    return {"data": data}


@router.post("/maps/city-spots")
async def maps_city_spots(payload: MapsCityRequest) -> dict[str, Any]:
    data = await MapsClient().city_productive_spots(city=payload.city, max_results=payload.max_results)
    return {"items": data, "count": len(data)}


@router.post("/maps/nearby-spots")
async def maps_nearby_spots(payload: MapsNearbyRequest) -> dict[str, Any]:
    data = await MapsClient().nearby_productive_spots(
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_meters=payload.radius_meters,
        max_results=payload.max_results,
    )
    return {"items": data, "count": len(data)}


@router.post("/maps/transit-duration")
async def maps_transit_duration(payload: MapsTransitRequest) -> dict[str, Any]:
    minutes = await MapsRoutesClient().transit_duration_minutes(
        origin_lat=payload.origin_lat,
        origin_lng=payload.origin_lng,
        destination_lat=payload.destination_lat,
        destination_lng=payload.destination_lng,
    )
    return {"minutes": minutes}


@router.post("/events/search")
async def events_search(payload: EventsSearchRequest) -> dict[str, Any]:
    data = await TicketmasterClient().search_events(
        city=payload.city,
        start_date=payload.start_date,
        end_date=payload.end_date,
        limit=payload.limit,
    )
    return {"items": data, "count": len(data)}


@router.post("/weather/five-day-forecast")
async def weather_five_day_forecast(payload: WeatherForecastRequest) -> dict[str, Any]:
    data = await OpenWeatherClient().five_day_forecast(city=payload.city)
    return {"data": data}


@router.post("/finance/exchange-rates")
async def finance_exchange_rates(payload: FinanceExchangeRequest) -> dict[str, Any]:
    data = await ExchangeRateClient().get_rates(payload.base_currency)
    return {
        "base_currency": payload.base_currency.upper(),
        "data": data,
        "rates": data.get("conversion_rates") if isinstance(data, dict) else None,
    }


@router.post("/finance/cost-baseline")
async def finance_cost_baseline(payload: FinanceBaselineRequest) -> dict[str, Any]:
    data = await fetch_numbeo_city_baseline(city=payload.city)
    return {"city": payload.city, "data": data}


@router.post("/safety/score")
async def safety_score(payload: SafetyScoreRequest) -> dict[str, Any]:
    data = await fetch_amadeus_safety_score(latitude=payload.latitude, longitude=payload.longitude)
    return {
        "data": data,
        "role": "secondary_signal",
        "explanation": "Amadeus safety score is optional and should not be used as the primary decision signal.",
    }


@router.post("/wellness/objective-signals")
async def wellness_objective_signals(payload: WellnessSignalsRequest) -> dict[str, Any]:
    data = await OpenWeatherClient().objective_wellness_signals(city=payload.city)
    return {
        "city": payload.city,
        "signals": data,
        "role": "primary_wellness_signal",
    }


@router.post("/environment/route-emissions")
async def environment_route_emissions(payload: EnvironmentRouteRequest) -> dict[str, Any]:
    data = await ClimatiqClient().estimate_route_emissions(distance_km=payload.distance_km, mode=payload.mode)
    return {"data": data}


@router.post("/rag/search-long-term")
async def rag_search_long_term(payload: RagSearchRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await FastMCPClient().call_tool(
        server_url=settings.mcp_rag_url,
        tool_name=settings.mcp_tool_rag_search_long_term,
        arguments={"query": payload.query, "limit": payload.limit},
        timeout_seconds=20,
    )
    return {"items": data if isinstance(data, list) else []}


@router.post("/rag/search-short-term")
async def rag_search_short_term(payload: RagSearchRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await FastMCPClient().call_tool(
        server_url=settings.mcp_rag_url,
        tool_name=settings.mcp_tool_rag_search_short_term,
        arguments={"query": payload.query, "limit": payload.limit},
        timeout_seconds=20,
    )
    return {"items": data if isinstance(data, list) else []}


@router.post("/rag/store")
async def rag_store(payload: RagStoreRequest) -> dict[str, Any]:
    settings = get_settings()
    data = await FastMCPClient().call_tool(
        server_url=settings.mcp_rag_url,
        tool_name=settings.mcp_tool_rag_store,
        arguments={
            "content": payload.content,
            "memory_type": payload.memory_type,
            "metadata": payload.metadata,
        },
        timeout_seconds=20,
    )
    return {"data": data}
