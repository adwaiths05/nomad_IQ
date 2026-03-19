from datetime import date
from typing import Any

import httpx

from app.config.settings import get_settings


class ExchangeRateClient:
    # Exchange rates are fetched every 12h and cached in Redis.
    cache_ttl_seconds = 12 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()

    async def get_rates(self, base_currency: str) -> dict[str, Any] | None:
        if not self.settings.exchange_rate_api_key:
            return None

        url = f"{self.settings.exchange_rate_base_url}/{self.settings.exchange_rate_api_key}/latest/{base_currency.upper()}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            if response.status_code >= 400:
                return None
            return response.json()


class GooglePlacesClient:
    # Opening hours and details are stable enough for 30-day cache windows.
    details_cache_ttl_seconds = 30 * 24 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()

    async def nearby_productive_spots(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 1500,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        if not self.settings.google_places_api_key:
            return []

        query = (
            "quiet library OR quiet cafe OR coworking space OR study cafe "
            "with low busyness and productive atmosphere"
        )
        url = f"{self.settings.google_places_base_url}/textsearch/json"
        params = {
            "query": query,
            "location": f"{latitude},{longitude}",
            "radius": radius_meters,
            "key": self.settings.google_places_api_key,
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, params=params)
            if response.status_code >= 400:
                return []
            data = response.json()

        rows: list[dict[str, Any]] = []
        for item in data.get("results", [])[:max_results]:
            rating = float(item.get("rating") or 0)
            if rating < 4.2:
                continue

            types = [t.lower() for t in item.get("types", [])]
            tags = []
            if "library" in types:
                tags.append("library")
            if "cafe" in types:
                tags.append("quiet cafe")
            if "coworking_space" in types or "point_of_interest" in types:
                tags.append("coworking")

            # Places API text search does not always expose amenities; keep a conservative wifi heuristic.
            name_l = str(item.get("name") or "").lower()
            has_wifi = (
                "wifi" in name_l
                or "co-work" in name_l
                or "cowork" in name_l
                or "library" in types
                or "cafe" in types
            )
            if not has_wifi:
                continue

            rows.append(
                {
                    "name": item.get("name"),
                    "rating": rating,
                    "user_ratings_total": item.get("user_ratings_total"),
                    "open_now": item.get("opening_hours", {}).get("open_now"),
                    "latitude": item.get("geometry", {}).get("location", {}).get("lat"),
                    "longitude": item.get("geometry", {}).get("location", {}).get("lng"),
                    "types": types,
                    "productive_tags": tags or ["quiet cafe"],
                    "has_wifi": has_wifi,
                }
            )
        return rows

    async def city_productive_spots(self, city: str, max_results: int = 10) -> list[dict[str, Any]]:
        if not self.settings.google_places_api_key:
            return []

        query = f"library OR cafe quiet study work friendly in {city}"
        url = f"{self.settings.google_places_base_url}/textsearch/json"
        params = {
            "query": query,
            "key": self.settings.google_places_api_key,
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, params=params)
            if response.status_code >= 400:
                return []
            data = response.json()

        rows: list[dict[str, Any]] = []
        for item in data.get("results", [])[:max_results]:
            rating = float(item.get("rating") or 0)
            if rating < 4.2:
                continue

            types = [t.lower() for t in item.get("types", [])]
            if not ("library" in types or "cafe" in types or "coworking_space" in types):
                continue

            name_l = str(item.get("name") or "").lower()
            has_wifi = (
                "wifi" in name_l
                or "co-work" in name_l
                or "cowork" in name_l
                or "library" in types
                or "cafe" in types
            )
            if not has_wifi:
                continue

            rows.append(
                {
                    "name": item.get("name"),
                    "rating": rating,
                    "open_now": item.get("opening_hours", {}).get("open_now"),
                    "latitude": item.get("geometry", {}).get("location", {}).get("lat"),
                    "longitude": item.get("geometry", {}).get("location", {}).get("lng"),
                    "types": types,
                    "productive_tags": [
                        "library" if "library" in types else "quiet cafe",
                    ],
                    "has_wifi": has_wifi,
                }
            )
        return rows


class GoogleRoutesClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def transit_duration_minutes(
        self,
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
    ) -> int | None:
        if not self.settings.google_routes_api_key:
            return None

        url = f"{self.settings.google_routes_base_url}/directions/v2:computeRoutes"
        headers = {
            "X-Goog-Api-Key": self.settings.google_routes_api_key,
            "X-Goog-FieldMask": "routes.duration",
            "Content-Type": "application/json",
        }
        payload = {
            "origin": {
                "location": {
                    "latLng": {
                        "latitude": origin_lat,
                        "longitude": origin_lng,
                    }
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": destination_lat,
                        "longitude": destination_lng,
                    }
                }
            },
            "travelMode": "TRANSIT",
            "routingPreference": "TRAFFIC_AWARE",
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code >= 400:
                return None
            data = response.json()

        routes = data.get("routes", [])
        if not routes:
            return None
        duration = routes[0].get("duration")
        if not isinstance(duration, str) or not duration.endswith("s"):
            return None
        try:
            seconds = int(float(duration[:-1]))
        except ValueError:
            return None
        return max(int(round(seconds / 60)), 1)


class TicketmasterClient:
    cache_ttl_seconds = 24 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()

    async def search_events(self, city: str, start_date: date, end_date: date, limit: int = 20) -> list[dict[str, Any]]:
        if not self.settings.ticketmaster_api_key:
            return []

        url = f"{self.settings.ticketmaster_base_url}/events.json"
        params = {
            "apikey": self.settings.ticketmaster_api_key,
            "city": city,
            "startDateTime": f"{start_date.isoformat()}T00:00:00Z",
            "endDateTime": f"{end_date.isoformat()}T23:59:59Z",
            "size": limit,
            "sort": "date,asc",
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, params=params)
            if response.status_code >= 400:
                return []
            data = response.json()

        items = data.get("_embedded", {}).get("events", [])
        rows: list[dict[str, Any]] = []
        for event in items:
            venues = event.get("_embedded", {}).get("venues", [])
            venue_name = venues[0].get("name") if venues else None
            rows.append(
                {
                    "name": event.get("name", "Event"),
                    "venue": venue_name,
                    "category": event.get("classifications", [{}])[0].get("segment", {}).get("name", "general"),
                    "description": event.get("info") or event.get("pleaseNote"),
                    "start_date": (event.get("dates", {}).get("start", {}).get("localDate") or start_date.isoformat()),
                    "end_date": (event.get("dates", {}).get("end", {}).get("localDate") or event.get("dates", {}).get("start", {}).get("localDate") or start_date.isoformat()),
                    "popularity": float(event.get("promoter", {}).get("id", 0) or 0),
                    "source": "ticketmaster",
                }
            )
        return rows


class OpenWeatherClient:
    cache_ttl_seconds = 12 * 60 * 60

    def __init__(self) -> None:
        self.settings = get_settings()

    async def five_day_forecast(self, city: str) -> dict[str, Any] | None:
        if not self.settings.openweather_api_key:
            return None

        url = f"{self.settings.openweather_base_url}/forecast"
        params = {
            "q": city,
            "appid": self.settings.openweather_api_key,
            "units": "metric",
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, params=params)
            if response.status_code >= 400:
                return None
            return response.json()


class ClimatiqClient:
    # Route emissions are deterministic enough to cache forever.
    cache_ttl_seconds: int | None = None

    def __init__(self) -> None:
        self.settings = get_settings()

    async def estimate_route_emissions(
        self,
        distance_km: float,
        mode: str = "passenger_train",
    ) -> dict[str, Any] | None:
        if not self.settings.climatiq_api_key:
            return None

        url = f"{self.settings.climatiq_base_url}/data/v1/estimate"
        headers = {
            "Authorization": f"Bearer {self.settings.climatiq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "emission_factor": {"activity_id": mode, "data_version": "^21"},
            "parameters": {"distance": distance_km, "distance_unit": "km"},
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code >= 400:
                return None
            return response.json()


async def fetch_numbeo_city_baseline(city: str) -> dict[str, Any] | None:
    settings = get_settings()
    if not settings.apify_api_token or not settings.numbeo_apify_actor_id:
        return None

    # This endpoint triggers/reads an Apify run output for Numbeo-like cost data.
    url = f"{settings.apify_base_url}/acts/{settings.numbeo_apify_actor_id}/run-sync-get-dataset-items"
    params = {"token": settings.apify_api_token}
    payload = {"city": city}

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, params=params, json=payload)
        if response.status_code >= 400:
            return None
        rows = response.json()

    if not rows:
        return None

    top = rows[0] if isinstance(rows, list) else rows
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
    if not settings.amadeus_api_key or not settings.amadeus_api_secret:
        return None

    token_url = f"{settings.amadeus_base_url}/v1/security/oauth2/token"
    score_url = f"{settings.amadeus_base_url}/v1/safety/safety-rated-locations"

    async with httpx.AsyncClient(timeout=20) as client:
        token_response = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.amadeus_api_key,
                "client_secret": settings.amadeus_api_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_response.status_code >= 400:
            return None

        token = token_response.json().get("access_token")
        if not token:
            return None

        score_response = await client.get(
            score_url,
            headers={"Authorization": f"Bearer {token}"},
            params={"latitude": latitude, "longitude": longitude},
        )
        if score_response.status_code >= 400:
            return None

        data = score_response.json().get("data", [])
        if not data:
            return None

        safety_scores = data[0].get("safetyScores", {})
        values = [float(v) for v in safety_scores.values() if isinstance(v, (int, float))]
        total = round(sum(values) / len(values), 2) if values else None
        return {
            "score": total,
            "scores": safety_scores,
            "source": "amadeus",
        }
