from datetime import date
from typing import Any

import httpx

from app.config.settings import get_settings
from app.integrations.mcp_client import FastMCPClient


def _date_to_str(value: date | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


class MapsClient:
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
            server_url=self.settings.mcp_travel_url,
            tool_name=self.settings.mcp_tool_travel_nearby_spots,
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
            server_url=self.settings.mcp_travel_url,
            tool_name=self.settings.mcp_tool_travel_city_spots,
            arguments={"city": city, "max_results": max_results},
            timeout_seconds=20,
        )
        return result if isinstance(result, list) else []


class MapsRoutesClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.mcp = FastMCPClient()

    async def transit_duration_minutes(
        self,
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
        mode: str = "walking",
    ) -> int | None:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_travel_url,
            tool_name=self.settings.mcp_tool_travel_transit_duration,
            arguments={
                "origin_lat": origin_lat,
                "origin_lng": origin_lng,
                "destination_lat": destination_lat,
                "destination_lng": destination_lng,
                "mode": mode,
            },
            timeout_seconds=20,
        )
        if isinstance(result, dict) and isinstance(result.get("minutes"), (int, float)):
            return int(result["minutes"])
        if isinstance(result, (int, float)):
            return int(result)
        return None


class TicketmasterClient:
    cache_ttl_seconds = 24 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()

    async def search_events(self, city: str, start_date: date, end_date: date, limit: int = 20) -> list[dict[str, Any]]:
        if not self.settings.ticketmaster_api_key:
            return []

        params = {
            "apikey": self.settings.ticketmaster_api_key,
            "city": city,
            "startDateTime": f"{_date_to_str(start_date)}T00:00:00Z",
            "endDateTime": f"{_date_to_str(end_date)}T23:59:59Z",
            "size": max(1, min(limit, 100)),
            "sort": "date,asc",
        }

        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.get(f"{self.settings.ticketmaster_base_url.rstrip('/')}/events.json", params=params)
            if response.status_code >= 400:
                return []
            payload = response.json()

        embedded = payload.get("_embedded") if isinstance(payload, dict) else None
        rows = embedded.get("events") if isinstance(embedded, dict) else None
        if not isinstance(rows, list):
            return []

        result: list[dict[str, Any]] = []
        for event in rows:
            if not isinstance(event, dict):
                continue
            venues = event.get("_embedded", {}).get("venues", []) if isinstance(event.get("_embedded"), dict) else []
            venue_name = venues[0].get("name") if isinstance(venues, list) and venues and isinstance(venues[0], dict) else None
            start_info = event.get("dates", {}).get("start", {}) if isinstance(event.get("dates"), dict) else {}
            local_date = start_info.get("localDate")
            parsed_start = str(local_date or _date_to_str(start_date))
            classifications = event.get("classifications") if isinstance(event.get("classifications"), list) else []
            category = "event"
            if classifications and isinstance(classifications[0], dict):
                segment = classifications[0].get("segment")
                if isinstance(segment, dict) and isinstance(segment.get("name"), str):
                    category = segment["name"].lower()

            result.append(
                {
                    "id": event.get("id"),
                    "name": event.get("name") or "Untitled Event",
                    "venue": venue_name,
                    "start_date": parsed_start,
                    "end_date": parsed_start,
                    "category": category,
                    "description": event.get("url"),
                    "popularity": event.get("test", False) and 0.2 or 0.7,
                    "source": "ticketmaster",
                }
            )
        return result


class EventbriteClient:
    cache_ttl_seconds = 12 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()

    async def search_events(self, city: str, start_date: date, end_date: date, limit: int = 20) -> list[dict[str, Any]]:
        if not self.settings.eventbrite_api_token:
            return []

        headers = {
            "Authorization": f"Bearer {self.settings.eventbrite_api_token}",
            "Content-Type": "application/json",
        }
        params = {
            "location.address": city,
            "start_date.range_start": f"{_date_to_str(start_date)}T00:00:00Z",
            "start_date.range_end": f"{_date_to_str(end_date)}T23:59:59Z",
            "expand": "venue,ticket_availability",
            "sort_by": "date",
            "page_size": max(1, min(limit, 50)),
        }

        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.get(f"{self.settings.eventbrite_base_url.rstrip('/')}/events/search/", headers=headers, params=params)
            if response.status_code >= 400:
                return []
            payload = response.json()

        rows = payload.get("events") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            return []

        result: list[dict[str, Any]] = []
        for event in rows:
            if not isinstance(event, dict):
                continue

            venue = event.get("venue") if isinstance(event.get("venue"), dict) else {}
            category = "local_event"
            if isinstance(event.get("category_id"), str) and event.get("category_id"):
                category = "local_event"

            start_block = event.get("start") if isinstance(event.get("start"), dict) else {}
            end_block = event.get("end") if isinstance(event.get("end"), dict) else {}
            ticket_block = event.get("ticket_availability") if isinstance(event.get("ticket_availability"), dict) else {}
            is_free = bool(event.get("is_free"))

            result.append(
                {
                    "id": event.get("id"),
                    "name": event.get("name", {}).get("text") if isinstance(event.get("name"), dict) else (event.get("name") or "Untitled Event"),
                    "venue": venue.get("name") or venue.get("address", {}).get("localized_address_display") if isinstance(venue.get("address"), dict) else venue.get("name"),
                    "start_date": start_block.get("local") or start_block.get("utc") or _date_to_str(start_date),
                    "end_date": end_block.get("local") or end_block.get("utc") or _date_to_str(end_date),
                    "category": category,
                    "description": event.get("url"),
                    "popularity": 0.55,
                    "price_hint": 0.0 if is_free else 300.0,
                    "ticket_status": ticket_block.get("is_sold_out") is False,
                    "source": "eventbrite",
                }
            )

        return result


class TransportClient:
    """India-centric land-based transport: trains, buses, metro"""
    cache_ttl_seconds = 2 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()
        self.mcp = FastMCPClient()

    async def search_trains(
        self,
        origin_city: str,
        destination_city: str,
        journey_date: date | str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_travel_url,
            tool_name=self.settings.mcp_tool_travel_search_trains,
            arguments={
                "origin_city": origin_city,
                "destination_city": destination_city,
                "journey_date": _date_to_str(journey_date),
                "limit": limit,
            },
            timeout_seconds=40,
        )
        return result if isinstance(result, list) else []

    async def search_buses(
        self,
        origin_city: str,
        destination_city: str,
        journey_date: date | str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_travel_url,
            tool_name=self.settings.mcp_tool_travel_search_buses,
            arguments={
                "origin_city": origin_city,
                "destination_city": destination_city,
                "journey_date": _date_to_str(journey_date),
                "limit": limit,
            },
            timeout_seconds=30,
        )
        return result if isinstance(result, list) else []

    async def search_metro(
        self,
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
        city: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_travel_url,
            tool_name=self.settings.mcp_tool_travel_search_metro,
            arguments={
                "origin_lat": origin_lat,
                "origin_lng": origin_lng,
                "destination_lat": destination_lat,
                "destination_lng": destination_lng,
                "city": city,
                "limit": limit,
            },
            timeout_seconds=30,
        )
        return result if isinstance(result, list) else []

    # Flight and nomad deals removed - India focus on land transport


class OpenWeatherClient:
    cache_ttl_seconds = 12 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()

    async def five_day_forecast(self, city: str) -> dict[str, Any] | None:
        if not self.settings.openweather_api_key:
            return {"city": city, "list": [], "source": "openweather_unconfigured"}

        params = {
            "q": city,
            "appid": self.settings.openweather_api_key,
            "units": "metric",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.settings.openweather_base_url.rstrip('/')}/forecast", params=params)
            if response.status_code >= 400:
                return {"city": city, "list": [], "source": "openweather"}
            payload = response.json()

        if isinstance(payload, dict):
            payload.setdefault("source", "openweather")
            return payload
        return {"city": city, "list": [], "source": "openweather"}

    async def objective_wellness_signals(self, city: str) -> dict[str, Any]:
        if not self.settings.openweather_api_key:
            return {
                "city": city,
                "aqi": None,
                "uv_index": None,
                "weather": None,
                "heat_index_c": None,
                "source": "openweather_unconfigured",
            }

        geo_params = {
            "q": city,
            "limit": 1,
            "appid": self.settings.openweather_api_key,
        }

        async with httpx.AsyncClient(timeout=20) as client:
            geo_response = await client.get(f"{self.settings.openweather_geo_base_url.rstrip('/')}/direct", params=geo_params)
            if geo_response.status_code >= 400:
                return {
                    "city": city,
                    "aqi": None,
                    "uv_index": None,
                    "weather": None,
                    "heat_index_c": None,
                    "source": "openweather",
                }

            geo_payload = geo_response.json()
            top = geo_payload[0] if isinstance(geo_payload, list) and geo_payload and isinstance(geo_payload[0], dict) else {}
            lat = top.get("lat")
            lon = top.get("lon")
            if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                return {
                    "city": city,
                    "aqi": None,
                    "uv_index": None,
                    "weather": None,
                    "heat_index_c": None,
                    "source": "openweather",
                }

            weather_response = await client.get(
                f"{self.settings.openweather_base_url.rstrip('/')}/weather",
                params={"lat": lat, "lon": lon, "appid": self.settings.openweather_api_key, "units": "metric"},
            )
            aqi_response = await client.get(
                f"{self.settings.openweather_base_url.rstrip('/')}/air_pollution",
                params={"lat": lat, "lon": lon, "appid": self.settings.openweather_api_key},
            )

        weather_payload = weather_response.json() if weather_response.status_code < 400 else {}
        aqi_payload = aqi_response.json() if aqi_response.status_code < 400 else {}

        aqi_list = aqi_payload.get("list") if isinstance(aqi_payload, dict) else []
        aqi_raw = aqi_list[0].get("main", {}).get("aqi") if isinstance(aqi_list, list) and aqi_list and isinstance(aqi_list[0], dict) else None
        weather_rows = weather_payload.get("weather") if isinstance(weather_payload, dict) else []
        weather_text = weather_rows[0].get("main") if isinstance(weather_rows, list) and weather_rows and isinstance(weather_rows[0], dict) else None
        temp = weather_payload.get("main", {}).get("temp") if isinstance(weather_payload, dict) else None
        feels_like = weather_payload.get("main", {}).get("feels_like") if isinstance(weather_payload, dict) else None

        return {
            "city": city,
            "latitude": lat,
            "longitude": lon,
            "aqi": int(aqi_raw) if isinstance(aqi_raw, (int, float)) else None,
            "uv_index": weather_payload.get("uvi") if isinstance(weather_payload, dict) else None,
            "weather": weather_text,
            "temperature_c": temp,
            "heat_index_c": feels_like,
            "source": "openweather",
        }


class ClimatiqClient:
    cache_ttl_seconds: int | None = None

    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def _fallback_emissions(distance_km: float, mode: str) -> dict[str, Any]:
        factors = {
            "passenger_train": 41.0,
            "car": 170.0,
            "bus": 105.0,
            "flight": 255.0,
        }
        factor = factors.get(mode, 120.0)
        co2e_kg = round((distance_km * factor) / 1000.0, 4)
        return {
            "distance_km": distance_km,
            "mode": mode,
            "co2e_kg": co2e_kg,
            "co2e_unit": "kg",
            "source": "deterministic_fallback",
        }

    async def estimate_route_emissions(
        self,
        distance_km: float,
        mode: str = "passenger_train",
    ) -> dict[str, Any] | None:
        if not self.settings.climatiq_api_key:
            return self._fallback_emissions(distance_km, mode)

        headers = {
            "Authorization": f"Bearer {self.settings.climatiq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "emission_factor": {
                "activity_id": f"passenger_vehicle-vehicle_type_{mode}",
            },
            "parameters": {
                "distance": distance_km,
                "distance_unit": "km",
            },
        }
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(
                f"{self.settings.climatiq_base_url.rstrip('/')}/data/v1/estimate",
                headers=headers,
                json=payload,
            )
            if response.status_code >= 400:
                return self._fallback_emissions(distance_km, mode)
            body = response.json()

        return {
            "distance_km": distance_km,
            "mode": mode,
            "co2e_kg": body.get("co2e"),
            "co2e_unit": body.get("co2e_unit", "kg"),
            "source": "climatiq",
            "raw": body,
        }


async def fetch_numbeo_city_baseline(city: str) -> dict[str, Any] | None:
    settings = get_settings()

    def _fallback() -> dict[str, Any]:
        return {
            "city": city,
            "currency": "USD",
            "daily_food": 35.0,
            "daily_transport": 12.0,
            "daily_lodging": 65.0,
            "daily_activities": 30.0,
            "source": "deterministic_fallback",
            "raw": {"reason": "apify_unconfigured"},
        }

    if not settings.apify_api_token or not settings.numbeo_city_cost_actor_id:
        return _fallback()

    headers = {
        "Authorization": f"Bearer {settings.apify_api_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=45) as client:
        start = await client.post(
            f"https://api.apify.com/v2/acts/{settings.numbeo_city_cost_actor_id}/runs",
            headers=headers,
            json={"city": city},
            params={"waitForFinish": 120},
        )
        if start.status_code >= 400:
            return _fallback()

        run = start.json()
        dataset_id = None
        if isinstance(run, dict):
            data = run.get("data") if isinstance(run.get("data"), dict) else run
            dataset_id = data.get("defaultDatasetId") if isinstance(data, dict) else None

        if not dataset_id:
            return _fallback()

        items = await client.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items",
            headers=headers,
            params={"clean": "true", "limit": 1},
        )
        if items.status_code >= 400:
            return _fallback()

        payload = items.json()
        row = payload[0] if isinstance(payload, list) and payload else {}
        if not isinstance(row, dict):
            return _fallback()

    return {
        "city": city,
        "currency": row.get("currency", "USD"),
        "daily_food": float(row.get("daily_food", 35.0)),
        "daily_transport": float(row.get("daily_transport", 12.0)),
        "daily_lodging": float(row.get("daily_lodging", 65.0)),
        "daily_activities": float(row.get("daily_activities", 30.0)),
        "source": "apify_numbeo",
        "raw": row,
    }


def _normalize_time_of_day(time_of_day: str | None, local_hour: int | None) -> str:
    if isinstance(time_of_day, str) and time_of_day.strip():
        return time_of_day.strip().lower()
    if local_hour is None:
        return "unknown"
    if 5 <= local_hour < 12:
        return "morning"
    if 12 <= local_hour < 17:
        return "afternoon"
    if 17 <= local_hour < 22:
        return "evening"
    return "night"


def _event_crowd_risk(event_count: int | None) -> float:
    if event_count is None:
        return 0.25
    return max(0.0, min(float(event_count) / 20.0, 1.0))


def _time_risk_bucket(time_bucket: str) -> float:
    mapping = {
        "morning": 0.15,
        "afternoon": 0.20,
        "evening": 0.35,
        "night": 0.55,
        "unknown": 0.30,
    }
    return mapping.get(time_bucket, 0.30)


def _location_type_risk(location_type: str | None) -> float:
    normalized = (location_type or "unknown").strip().lower()
    mapping = {
        "tourist": 0.35,
        "residential": 0.20,
        "commercial": 0.25,
        "isolated": 0.60,
        "transit_hub": 0.45,
        "unknown": 0.30,
    }
    return mapping.get(normalized, 0.30)


async def fetch_contextual_safety_score(
    latitude: float,
    longitude: float,
    *,
    city: str | None = None,
    event_count: int | None = None,
    time_of_day: str | None = None,
    location_type: str | None = None,
) -> dict[str, Any] | None:
    settings = get_settings()
    if not settings.safety_secondary_signal_enabled:
        return None

    if not settings.openweather_api_key:
        return {
            "score": None,
            "core_signals": {
                "aqi": None,
                "uv_index": None,
                "temperature_c": None,
                "heat_index_c": None,
            },
            "context_signals": {
                "event_count": event_count,
                "time_of_day": time_of_day or "unknown",
                "location_type": location_type or "unknown",
            },
            "source": "openweather_unconfigured",
            "note": "secondary_signal_only",
        }

    async with httpx.AsyncClient(timeout=25) as client:
        weather_response = await client.get(
            f"{settings.openweather_base_url.rstrip('/')}/weather",
            params={"lat": latitude, "lon": longitude, "appid": settings.openweather_api_key, "units": "metric"},
        )
        aqi_response = await client.get(
            f"{settings.openweather_base_url.rstrip('/')}/air_pollution",
            params={"lat": latitude, "lon": longitude, "appid": settings.openweather_api_key},
        )
        onecall_response = await client.get(
            f"{settings.openweather_onecall_base_url.rstrip('/')}/onecall",
            params={
                "lat": latitude,
                "lon": longitude,
                "exclude": "minutely,hourly,daily,alerts",
                "appid": settings.openweather_api_key,
                "units": "metric",
            },
        )

    weather_payload = weather_response.json() if weather_response.status_code < 400 else {}
    aqi_payload = aqi_response.json() if aqi_response.status_code < 400 else {}
    onecall_payload = onecall_response.json() if onecall_response.status_code < 400 else {}

    weather_main = weather_payload.get("main") if isinstance(weather_payload, dict) and isinstance(weather_payload.get("main"), dict) else {}
    aqi_list = aqi_payload.get("list") if isinstance(aqi_payload, dict) and isinstance(aqi_payload.get("list"), list) else []
    current = onecall_payload.get("current") if isinstance(onecall_payload, dict) and isinstance(onecall_payload.get("current"), dict) else {}

    aqi_value = None
    if aqi_list and isinstance(aqi_list[0], dict):
        main_block = aqi_list[0].get("main")
        if isinstance(main_block, dict) and isinstance(main_block.get("aqi"), (int, float)):
            aqi_value = int(main_block.get("aqi"))

    uv_index = current.get("uvi") if isinstance(current.get("uvi"), (int, float)) else None
    temp_c = weather_main.get("temp") if isinstance(weather_main.get("temp"), (int, float)) else None
    heat_index_c = weather_main.get("feels_like") if isinstance(weather_main.get("feels_like"), (int, float)) else None

    timezone_offset = weather_payload.get("timezone") if isinstance(weather_payload, dict) and isinstance(weather_payload.get("timezone"), (int, float)) else 0
    local_hour = None
    if isinstance(timezone_offset, (int, float)):
        from datetime import datetime, timezone, timedelta

        local_time = datetime.now(timezone.utc) + timedelta(seconds=float(timezone_offset))
        local_hour = int(local_time.hour)

    normalized_time = _normalize_time_of_day(time_of_day, local_hour)

    aqi_risk = max(0.0, min(((aqi_value or 3) - 1) / 4.0, 1.0))
    uv_risk = max(0.0, min((float(uv_index) if uv_index is not None else 5.0) / 11.0, 1.0))
    heat_anchor = float(heat_index_c) if heat_index_c is not None else (float(temp_c) if temp_c is not None else 28.0)
    heat_risk = max(0.0, min((heat_anchor - 22.0) / 18.0, 1.0))

    crowd_risk = _event_crowd_risk(event_count)
    time_risk = _time_risk_bucket(normalized_time)
    location_risk = _location_type_risk(location_type)

    core_risk = (0.4 * aqi_risk) + (0.3 * uv_risk) + (0.3 * heat_risk)
    context_risk = (0.45 * crowd_risk) + (0.25 * time_risk) + (0.30 * location_risk)
    combined_risk = (0.70 * core_risk) + (0.30 * context_risk)
    safety_score = round(max(0.0, min((1.0 - combined_risk) * 100.0, 100.0)), 2)

    return {
        "score": safety_score,
        "core_signals": {
            "aqi": aqi_value,
            "uv_index": uv_index,
            "temperature_c": temp_c,
            "heat_index_c": heat_index_c,
        },
        "context_signals": {
            "event_count": event_count,
            "crowd_risk": round(crowd_risk, 3),
            "time_of_day": normalized_time,
            "time_risk": round(time_risk, 3),
            "location_type": (location_type or "unknown").strip().lower(),
            "location_risk": round(location_risk, 3),
            "city": city,
        },
        "source": "openweather_plus_context",
        "note": "secondary_signal_only",
    }
