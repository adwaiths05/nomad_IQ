from datetime import date
from typing import Any

from app.config.settings import get_settings
from app.integrations.mcp_client import FastMCPClient


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
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_google_maps_server_url,
            tool_name=self.settings.mcp_tool_google_places_nearby,
            arguments={
                "latitude": latitude,
                "longitude": longitude,
                "radius_meters": radius_meters,
                "max_results": max_results,
            },
            timeout_seconds=20,
        )
        return result if isinstance(result, list) else []

    async def city_productive_spots(self, city: str, max_results: int = 10) -> list[dict[str, Any]]:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_google_maps_server_url,
            tool_name=self.settings.mcp_tool_google_places_city,
            arguments={
                "city": city,
                "max_results": max_results,
            },
            timeout_seconds=20,
        )
        return result if isinstance(result, list) else []


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
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_google_maps_server_url,
            tool_name=self.settings.mcp_tool_google_routes_transit,
            arguments={
                "origin_lat": origin_lat,
                "origin_lng": origin_lng,
                "destination_lat": destination_lat,
                "destination_lng": destination_lng,
            },
            timeout_seconds=20,
        )

        if isinstance(result, int):
            return max(result, 1)
        if isinstance(result, float):
            return max(int(round(result)), 1)
        if isinstance(result, dict):
            minutes = result.get("minutes")
            if isinstance(minutes, (int, float)):
                return max(int(round(minutes)), 1)
        return None


class TicketmasterClient:
    cache_ttl_seconds = 24 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()
        self.mcp = FastMCPClient()

    async def search_events(self, city: str, start_date: date, end_date: date, limit: int = 20) -> list[dict[str, Any]]:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_composio_server_url,
            tool_name=self.settings.mcp_tool_ticketmaster_events,
            arguments={
                "city": city,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "limit": limit,
            },
            timeout_seconds=20,
        )
        return result if isinstance(result, list) else []


class OpenWeatherClient:
    cache_ttl_seconds = 12 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()
        self.mcp = FastMCPClient()

    async def five_day_forecast(self, city: str) -> dict[str, Any] | None:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_composio_server_url,
            tool_name=self.settings.mcp_tool_openweather_forecast,
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
    result = await FastMCPClient().call_tool(
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
