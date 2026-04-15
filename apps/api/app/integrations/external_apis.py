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


class ExchangeRateClient:
    cache_ttl_seconds = 12 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()

    async def get_rates(self, base_currency: str) -> dict[str, Any] | None:
        base = (base_currency or "USD").upper()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.settings.exchange_api_base_url.rstrip('/')}/latest/{base}")
            if response.status_code >= 400:
                return {"base_code": base, "conversion_rates": {base: 1.0}, "source": "fallback"}
            payload = response.json()

        rates = payload.get("rates") or payload.get("conversion_rates") or {}
        if not isinstance(rates, dict):
            rates = {base: 1.0}

        return {
            "base_code": payload.get("base_code") or payload.get("base") or base,
            "conversion_rates": rates,
            "source": "open_er_api",
        }


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
    ) -> int | None:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_travel_url,
            tool_name=self.settings.mcp_tool_travel_transit_duration,
            arguments={
                "origin_lat": origin_lat,
                "origin_lng": origin_lng,
                "destination_lat": destination_lat,
                "destination_lng": destination_lng,
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


class TransportClient:
    cache_ttl_seconds = 2 * 60 * 60
    nomad_cache_ttl_seconds = 6 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()
        self.mcp = FastMCPClient()

    async def search_flights(
        self,
        city: str,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        origin_city: str | None = None,
        limit: int = 10,
        currency: str = "USD",
    ) -> list[dict[str, Any]]:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_travel_url,
            tool_name=self.settings.mcp_tool_travel_search_flights,
            arguments={
                "city": city,
                "start_date": _date_to_str(start_date),
                "end_date": _date_to_str(end_date),
                "origin_city": origin_city,
                "limit": limit,
                "currency": currency,
            },
            timeout_seconds=40,
        )
        return result if isinstance(result, list) else []

    async def search_nomad_deals(
        self,
        origin_city: str | None = None,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        nights_in_dst_from: int | None = None,
        nights_in_dst_to: int | None = None,
        max_fly_duration: int | None = None,
        limit: int = 10,
        currency: str = "USD",
    ) -> dict[str, Any] | list[Any] | None:
        result = await self.mcp.call_tool(
            server_url=self.settings.mcp_travel_url,
            tool_name=self.settings.mcp_tool_travel_search_nomad_deals,
            arguments={
                "origin_city": origin_city,
                "start_date": _date_to_str(start_date),
                "end_date": _date_to_str(end_date),
                "nights_in_dst_from": nights_in_dst_from,
                "nights_in_dst_to": nights_in_dst_to,
                "max_fly_duration": max_fly_duration,
                "limit": limit,
                "currency": currency,
            },
            timeout_seconds=40,
        )
        return result if isinstance(result, (dict, list)) else None


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


async def _amadeus_token(settings) -> str | None:
    if not settings.amadeus_client_id or not settings.amadeus_client_secret:
        return None

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{settings.amadeus_base_url.rstrip('/')}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.amadeus_client_id,
                "client_secret": settings.amadeus_client_secret,
            },
        )
        if response.status_code >= 400:
            return None
        body = response.json()

    token = body.get("access_token") if isinstance(body, dict) else None
    return str(token) if token else None


async def fetch_amadeus_safety_score(latitude: float, longitude: float) -> dict[str, Any] | None:
    settings = get_settings()
    if not settings.safety_secondary_signal_enabled:
        return None

    token = await _amadeus_token(settings)
    if not token:
        return {
            "score": None,
            "scores": {},
            "source": "amadeus_unconfigured",
            "note": "secondary_signal_only",
        }

    headers = {"Authorization": f"Bearer {token}"}
    params = {"latitude": latitude, "longitude": longitude}
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.get(
            f"{settings.amadeus_base_url.rstrip('/')}/v1/safety/safety-rated-locations",
            headers=headers,
            params=params,
        )
        if response.status_code >= 400:
            return {
                "score": None,
                "scores": {},
                "source": "amadeus",
                "note": "secondary_signal_only",
            }
        payload = response.json()

    rows = payload.get("data") if isinstance(payload, dict) else None
    top = rows[0] if isinstance(rows, list) and rows and isinstance(rows[0], dict) else {}
    safety_scores = top.get("safetyScores") if isinstance(top.get("safetyScores"), dict) else {}
    values = [float(v) for v in safety_scores.values() if isinstance(v, (int, float))]
    total = round(sum(values) / len(values), 2) if values else None
    return {
        "score": total,
        "scores": safety_scores,
        "source": "amadeus",
        "note": "secondary_signal_only",
    }
