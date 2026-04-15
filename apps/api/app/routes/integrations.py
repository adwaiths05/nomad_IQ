from datetime import date
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.integrations.external_apis import (
    ClimatiqClient,
    ExchangeRateClient,
    EventbriteClient,
    MapsClient,
    MapsRoutesClient,
    OpenWeatherClient,
    TicketmasterClient,
    TransportClient,
    fetch_contextual_safety_score,
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


class EventsDiscoveryRequest(BaseModel):
    city: str
    start_date: date
    end_date: date
    latitude: float | None = None
    longitude: float | None = None
    budget_cap: float | None = None
    time_of_day: str | None = None
    location_type: str = "tourist"
    max_results: int = 5


class WeatherForecastRequest(BaseModel):
    city: str


class FinanceExchangeRequest(BaseModel):
    base_currency: str = "USD"


class FinanceBaselineRequest(BaseModel):
    city: str


class SafetyScoreRequest(BaseModel):
    latitude: float
    longitude: float
    city: str | None = None
    event_count: int | None = None
    time_of_day: str | None = None
    location_type: str | None = None


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


@router.post("/events/search-local")
async def events_search_local(payload: EventsSearchRequest) -> dict[str, Any]:
    data = await EventbriteClient().search_events(
        city=payload.city,
        start_date=payload.start_date,
        end_date=payload.end_date,
        limit=payload.limit,
    )
    return {"items": data, "count": len(data)}


def _default_festival_calendar(city: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
    return [
        {
            "id": f"festival-{city.lower()}-{start_date.isoformat()}",
            "name": f"{city} weekend community fest",
            "venue": city,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "category": "festival",
            "description": "Fallback local festival calendar entry.",
            "popularity": 0.5,
            "price_hint": 200.0,
            "source": "static_festival",
        }
    ]


def _score_discovery_candidate(
    *,
    event: dict[str, Any],
    weather_signals: dict[str, Any] | None,
    safety_payload: dict[str, Any] | None,
    budget_cap: float | None,
    crowd_count: int,
) -> float:
    weather = weather_signals or {}
    aqi = weather.get("aqi")
    heat = weather.get("heat_index_c")
    aqi_penalty = min(max(((float(aqi) if isinstance(aqi, (int, float)) else 3.0) - 1.0) / 4.0, 0.0), 1.0)
    heat_penalty = min(max(((float(heat) if isinstance(heat, (int, float)) else 28.0) - 22.0) / 18.0, 0.0), 1.0)

    event_price = event.get("price_hint")
    if not isinstance(event_price, (int, float)):
        event_price = 300.0 if event.get("source") == "eventbrite" else 500.0

    budget_ratio = 0.5
    if isinstance(budget_cap, (int, float)) and budget_cap > 0:
        budget_ratio = min(float(event_price) / float(budget_cap), 2.0)
    budget_penalty = min(max(budget_ratio / 2.0, 0.0), 1.0)

    crowd_penalty = min(max(float(crowd_count) / 25.0, 0.0), 1.0)
    uniqueness_bonus = 0.2 if event.get("source") == "eventbrite" else 0.1
    safety_score = safety_payload.get("score") if isinstance(safety_payload, dict) else None
    safety_boost = (float(safety_score) / 100.0) if isinstance(safety_score, (int, float)) else 0.5

    base = 0.45 * (1.0 - budget_penalty) + 0.20 * (1.0 - aqi_penalty) + 0.15 * (1.0 - heat_penalty) + 0.20 * (1.0 - crowd_penalty)
    total = max(0.0, min(base + uniqueness_bonus + (0.1 * safety_boost), 1.5))
    return round(total * 100.0, 2)


@router.post("/events/discover")
async def events_discover(payload: EventsDiscoveryRequest) -> dict[str, Any]:
    ticketmaster = await TicketmasterClient().search_events(
        city=payload.city,
        start_date=payload.start_date,
        end_date=payload.end_date,
        limit=max(1, payload.max_results * 2),
    )
    eventbrite = await EventbriteClient().search_events(
        city=payload.city,
        start_date=payload.start_date,
        end_date=payload.end_date,
        limit=max(1, payload.max_results * 2),
    )
    festivals = _default_festival_calendar(payload.city, payload.start_date, payload.end_date)

    merged_events = [*ticketmaster, *eventbrite, *festivals]

    if payload.latitude is not None and payload.longitude is not None:
        places = await MapsClient().nearby_productive_spots(
            latitude=payload.latitude,
            longitude=payload.longitude,
            radius_meters=1500,
            max_results=max(5, payload.max_results),
        )
    else:
        places = await MapsClient().city_productive_spots(payload.city, max_results=max(5, payload.max_results))

    cost_baseline = await fetch_numbeo_city_baseline(payload.city)
    wellness = await OpenWeatherClient().objective_wellness_signals(payload.city)
    safety = await fetch_contextual_safety_score(
        latitude=payload.latitude if payload.latitude is not None else 0.0,
        longitude=payload.longitude if payload.longitude is not None else 0.0,
        city=payload.city,
        event_count=len(merged_events),
        time_of_day=payload.time_of_day,
        location_type=payload.location_type,
    )

    recommendations: list[dict[str, Any]] = []
    for idx, event in enumerate(merged_events[: max(5, payload.max_results * 2)]):
        place = places[idx % len(places)] if places else None
        discovery_score = _score_discovery_candidate(
            event=event,
            weather_signals=wellness,
            safety_payload=safety,
            budget_cap=payload.budget_cap,
            crowd_count=len(merged_events),
        )

        daily_food = cost_baseline.get("daily_food") if isinstance(cost_baseline, dict) else None
        transport = cost_baseline.get("daily_transport") if isinstance(cost_baseline, dict) else None
        price_hint = event.get("price_hint") if isinstance(event.get("price_hint"), (int, float)) else 300.0
        estimated_total = float(price_hint) + float(daily_food or 35.0) + float(transport or 12.0)

        recommendations.append(
            {
                "event": event,
                "place": place,
                "estimated_cost": round(estimated_total, 2),
                "estimated_transit_minutes": 8 + (idx % 4) * 4,
                "crowd_level": "low" if len(merged_events) < 8 else ("medium" if len(merged_events) < 16 else "high"),
                "discovery_score": discovery_score,
            }
        )

    recommendations.sort(key=lambda row: float(row.get("discovery_score") or 0.0), reverse=True)
    top = recommendations[: max(1, payload.max_results)]

    return {
        "city": payload.city,
        "window": {"start_date": payload.start_date.isoformat(), "end_date": payload.end_date.isoformat()},
        "signals": {
            "events": {
                "ticketmaster_count": len(ticketmaster),
                "eventbrite_count": len(eventbrite),
                "festival_count": len(festivals),
            },
            "places_count": len(places),
            "cost_baseline": cost_baseline,
            "weather": wellness,
            "safety": safety,
            "time_of_day": payload.time_of_day,
            "location_type": payload.location_type,
        },
        "recommendations": top,
        "engine": "local_event_intelligence_layer",
    }


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
    data = await fetch_contextual_safety_score(
        latitude=payload.latitude,
        longitude=payload.longitude,
        city=payload.city,
        event_count=payload.event_count,
        time_of_day=payload.time_of_day,
        location_type=payload.location_type,
    )
    return {
        "data": data,
        "role": "secondary_signal",
        "explanation": "Safety combines OpenWeather core signals (AQI, UV, heat) with context signals (events, time, location type).",
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
