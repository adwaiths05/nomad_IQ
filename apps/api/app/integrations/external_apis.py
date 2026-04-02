from datetime import date
from typing import Any

from app.config.settings import get_settings
from app.integrations.mcp_client import FastMCPClient


def _parse_aliases(csv_value: str | None) -> list[str]:
    if not csv_value:
        return []
    return [chunk.strip() for chunk in csv_value.split(",") if chunk.strip()]


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_iso_date(value: Any) -> str:
    if isinstance(value, str) and value:
        return value[:10]
    return date.today().isoformat()


def _extract_ticketmaster_events(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if isinstance(result, dict):
        embedded = result.get("_embedded")
        if isinstance(embedded, dict) and isinstance(embedded.get("events"), list):
            return [item for item in embedded["events"] if isinstance(item, dict)]
    return []


def _normalize_ticketmaster_events(raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for event in raw_events:
        dates = event.get("dates") if isinstance(event.get("dates"), dict) else {}
        start_info = dates.get("start") if isinstance(dates.get("start"), dict) else {}
        end_info = dates.get("end") if isinstance(dates.get("end"), dict) else {}
        start_date = _to_iso_date(start_info.get("localDate") or start_info.get("dateTime"))
        end_date = _to_iso_date(end_info.get("localDate") or start_info.get("localDate") or start_info.get("dateTime"))

        venues = []
        embedded = event.get("_embedded")
        if isinstance(embedded, dict) and isinstance(embedded.get("venues"), list):
            venues = [v for v in embedded["venues"] if isinstance(v, dict)]
        venue_name = venues[0].get("name") if venues else None

        classifications = []
        if isinstance(event.get("classifications"), list):
            classifications = [c for c in event["classifications"] if isinstance(c, dict)]
        segment = classifications[0].get("segment") if classifications else {}
        category = segment.get("name") if isinstance(segment, dict) else None

        popularity = _to_float(event.get("popularity") or event.get("relevance"))

        normalized.append(
            {
                "name": str(event.get("name") or "Untitled event"),
                "venue": venue_name,
                "start_date": start_date,
                "end_date": end_date,
                "category": str(category or "general"),
                "description": event.get("info") or event.get("pleaseNote"),
                "popularity": popularity if popularity is not None else 0,
            }
        )
    return normalized


def _extract_maps_places(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if isinstance(result, dict):
        for key in ["places", "results", "candidates"]:
            value = result.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _normalize_maps_places(raw_places: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for place in raw_places:
        location = {}
        geometry = place.get("geometry") if isinstance(place.get("geometry"), dict) else {}
        if isinstance(geometry.get("location"), dict):
            location = geometry["location"]
        normalized.append(
            {
                "name": place.get("name") or place.get("displayName") or "Unknown place",
                "address": place.get("formatted_address") or place.get("formattedAddress") or place.get("vicinity"),
                "rating": _to_float(place.get("rating")),
                "latitude": _to_float(location.get("lat")),
                "longitude": _to_float(location.get("lng")),
                "types": place.get("types") if isinstance(place.get("types"), list) else [],
            }
        )
    return normalized


def _extract_duration_minutes(result: Any) -> int | None:
    if isinstance(result, int):
        return max(result, 1)
    if isinstance(result, float):
        return max(int(round(result)), 1)
    if isinstance(result, dict):
        if isinstance(result.get("minutes"), (int, float)):
            return max(int(round(float(result["minutes"]))), 1)

        rows = result.get("rows")
        if isinstance(rows, list) and rows:
            elements = rows[0].get("elements") if isinstance(rows[0], dict) else None
            if isinstance(elements, list) and elements:
                duration = elements[0].get("duration") if isinstance(elements[0], dict) else None
                if isinstance(duration, dict):
                    seconds = _to_float(duration.get("value"))
                    if seconds is not None and seconds > 0:
                        return max(int(round(seconds / 60)), 1)
    return None


class ExchangeRateClient:
    # Exchange rates are fetched every 12h and cached in Redis.
    cache_ttl_seconds = 12 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()
        self.mcp = FastMCPClient()

    async def get_rates(self, base_currency: str) -> dict[str, Any] | None:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_custom_server_url,
            tool_name=self.settings.mcp_tool_exchange_rates,
            arguments={"base_currency": base_currency.upper()},
            timeout_seconds=20,
        )
        return result if isinstance(result, dict) else None


class GooglePlacesClient:
    # Opening hours and details are stable enough for 30-day cache windows.
    details_cache_ttl_seconds = 30 * 24 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()
        self.mcp = FastMCPClient()

    async def nearby_productive_spots(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 1500,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        query = f"productive spots near {latitude},{longitude} within {radius_meters} meters"
        attempts = [
            {
                "query": query,
                "location": {"lat": latitude, "lng": longitude},
                "radius": radius_meters,
                "max_results": max_results,
            },
            {
                "query": query,
                "latitude": latitude,
                "longitude": longitude,
                "radius_meters": radius_meters,
                "max_results": max_results,
            },
            {
                "query": query,
            },
        ]
        for arguments in attempts:
            result = await self.mcp.call_tool(
                server_url=self.settings.mcp_google_maps_server_url,
                tool_name=self.settings.mcp_tool_google_places_nearby,
                tool_aliases=_parse_aliases(self.settings.mcp_tool_google_places_nearby_aliases),
                arguments=arguments,
                timeout_seconds=20,
            )
            places = _normalize_maps_places(_extract_maps_places(result))
            if places:
                return places[:max_results]
        return []

    async def city_productive_spots(self, city: str, max_results: int = 10) -> list[dict[str, Any]]:
        attempts = [
            {
                "query": f"best productive places in {city}",
                "max_results": max_results,
            },
            {
                "query": city,
                "max_results": max_results,
            },
            {
                "city": city,
                "max_results": max_results,
            },
        ]
        for arguments in attempts:
            result = await self.mcp.call_tool(
                server_url=self.settings.mcp_google_maps_server_url,
                tool_name=self.settings.mcp_tool_google_places_city,
                tool_aliases=_parse_aliases(self.settings.mcp_tool_google_places_city_aliases),
                arguments=arguments,
                timeout_seconds=20,
            )
            places = _normalize_maps_places(_extract_maps_places(result))
            if places:
                return places[:max_results]
        return []


class GoogleRoutesClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.mcp = FastMCPClient()

    async def transit_duration_minutes(
        self,
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
    ) -> int | None:
        attempts = [
            {
                "origins": [f"{origin_lat},{origin_lng}"],
                "destinations": [f"{destination_lat},{destination_lng}"],
                "mode": "transit",
            },
            {
                "origin": f"{origin_lat},{origin_lng}",
                "destination": f"{destination_lat},{destination_lng}",
                "mode": "transit",
            },
            {
                "origin_lat": origin_lat,
                "origin_lng": origin_lng,
                "destination_lat": destination_lat,
                "destination_lng": destination_lng,
            },
        ]
        for arguments in attempts:
            result = await self.mcp.call_tool(
                server_url=self.settings.mcp_google_maps_server_url,
                tool_name=self.settings.mcp_tool_google_routes_transit,
                tool_aliases=_parse_aliases(self.settings.mcp_tool_google_routes_transit_aliases),
                arguments=arguments,
                timeout_seconds=20,
            )
            minutes = _extract_duration_minutes(result)
            if minutes is not None:
                return minutes
        return None


class TicketmasterClient:
    cache_ttl_seconds = 24 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()
        self.mcp = FastMCPClient()

    async def search_events(self, city: str, start_date: date, end_date: date, limit: int = 20) -> list[dict[str, Any]]:
        server_url = self.settings.mcp_ticketmaster_server_url or self.settings.mcp_composio_server_url
        result = await self.mcp.call_tool(
            server_url=server_url,
            tool_name=self.settings.mcp_tool_ticketmaster_events,
            tool_aliases=_parse_aliases(self.settings.mcp_tool_ticketmaster_events_aliases),
            arguments={
                "city": city,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "size": limit,
                "limit": limit,
                "page": 0,
            },
            timeout_seconds=20,
        )
        raw_events = _extract_ticketmaster_events(result)
        return _normalize_ticketmaster_events(raw_events)


class OpenWeatherClient:
    cache_ttl_seconds = 12 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()
        self.mcp = FastMCPClient()

    async def five_day_forecast(self, city: str) -> dict[str, Any] | None:
        server_url = self.settings.mcp_openweather_server_url or self.settings.mcp_composio_server_url
        result = await self.mcp.call_tool(
            server_url=server_url,
            tool_name=self.settings.mcp_tool_openweather_forecast,
            tool_aliases=_parse_aliases(self.settings.mcp_tool_openweather_forecast_aliases),
            arguments={"city": city},
            timeout_seconds=20,
        )
        return result if isinstance(result, dict) else None


class ClimatiqClient:
    # Route emissions are deterministic enough to cache forever.
    cache_ttl_seconds: int | None = None

    def __init__(self) -> None:
        self.settings = get_settings()
        self.mcp = FastMCPClient()

    async def estimate_route_emissions(
        self,
        distance_km: float,
        mode: str = "passenger_train",
    ) -> dict[str, Any] | None:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_custom_server_url,
            tool_name=self.settings.mcp_tool_climatiq_emissions,
            arguments={
                "distance_km": distance_km,
                "mode": mode,
            },
            timeout_seconds=20,
        )
        return result if isinstance(result, dict) else None


async def fetch_numbeo_city_baseline(city: str) -> dict[str, Any] | None:
    settings = get_settings()
    client = FastMCPClient()

    # Prefer Apify prebuilt MCP workflow when configured.
    result: Any | None = None
    if settings.mcp_apify_server_url and settings.mcp_apify_numbeo_actor_id:
        run = await client.call_tool(
            server_url=settings.mcp_apify_server_url,
            tool_name=settings.mcp_tool_apify_call_actor,
            arguments={
                "actorId": settings.mcp_apify_numbeo_actor_id,
                "input": {"city": city},
            },
            timeout_seconds=60,
        )

        run_id = None
        if isinstance(run, dict):
            run_id = run.get("id") or run.get("runId")
            data = run.get("data")
            if not run_id and isinstance(data, dict):
                run_id = data.get("id") or data.get("runId")

        if run_id:
            output = await client.call_tool(
                server_url=settings.mcp_apify_server_url,
                tool_name=settings.mcp_tool_apify_get_actor_output,
                arguments={"runId": run_id},
                timeout_seconds=60,
            )
            if output is not None:
                result = output

    if result is None:
        result = await client.call_tool(
            server_url=settings.mcp_composio_server_url,
            tool_name=settings.mcp_tool_numbeo_baseline,
            arguments={"city": city},
            timeout_seconds=60,
        )

    if result is None:
        return None

    top = result[0] if isinstance(result, list) and result else result
    if not isinstance(top, dict):
        return None

    return {
        "city": city,
        "currency": top.get("currency", "USD"),
        "daily_food": float(top.get("daily_food", 35)),
        "daily_transport": float(top.get("daily_transport", 12)),
        "daily_lodging": float(top.get("daily_lodging", 65)),
        "daily_activities": float(top.get("daily_activities", 30)),
        "source": "numbeo_apify",
        "raw": top,
    }


async def fetch_amadeus_safety_score(latitude: float, longitude: float) -> dict[str, Any] | None:
    settings = get_settings()
    result = await FastMCPClient().call_tool(
        server_url=settings.mcp_custom_server_url,
        tool_name=settings.mcp_tool_amadeus_safety,
        arguments={
            "latitude": latitude,
            "longitude": longitude,
        },
        timeout_seconds=20,
    )
    if not isinstance(result, dict):
        return None

    if "score" in result and "scores" in result:
        return {
            "score": result.get("score"),
            "scores": result.get("scores") or {},
            "source": result.get("source") or "amadeus_mcp",
        }

    safety_scores = result.get("safetyScores") if isinstance(result.get("safetyScores"), dict) else {}
    values = [float(v) for v in safety_scores.values() if isinstance(v, (int, float))]
    total = round(sum(values) / len(values), 2) if values else None
    return {
        "score": total,
        "scores": safety_scores,
        "source": "amadeus_mcp",
    }
