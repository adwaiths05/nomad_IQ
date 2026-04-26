import os
from datetime import date, timedelta
from math import atan2, cos, radians, sin, sqrt
from typing import Any

import httpx
from fastmcp import FastMCP  # type: ignore[import-not-found]


mcp = FastMCP("mcp-travel")

INDIAN_RAILWAYS_BASE_URL = os.environ.get("INDIAN_RAILWAYS_BASE_URL", "").rstrip("/")
INDIAN_RAILWAYS_API_KEY = os.environ.get("INDIAN_RAILWAYS_API_KEY", "").strip()

OPENROUTESERVICE_BASE_URL = os.environ.get("OPENROUTESERVICE_BASE_URL", "https://api.openrouteservice.org").rstrip("/")
OPENROUTESERVICE_API_KEY = os.environ.get("OPENROUTESERVICE_API_KEY", "").strip()
OPENROUTESERVICE_BUS_PROFILE = os.environ.get("OPENROUTESERVICE_BUS_PROFILE", "driving-car").strip() or "driving-car"
OPENROUTESERVICE_METRO_PROFILE = os.environ.get("OPENROUTESERVICE_METRO_PROFILE", "driving-car").strip() or "driving-car"
OPENROUTESERVICE_WALKING_PROFILE = os.environ.get("OPENROUTESERVICE_WALKING_PROFILE", "foot-walking").strip() or "foot-walking"

PHOTON_BASE_URL = os.environ.get("PHOTON_BASE_URL", "https://photon.komoot.io").rstrip("/")
TRAVEL_HEADERS = {"User-Agent": "nomadiq-mcp-travel/1.0"}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius * c


def _resolve_date(value: str | None, default_days: int) -> str:
    if value:
        return value[:10]
    return (date.today() + timedelta(days=default_days)).isoformat()


async def _resolve_city_coordinates(city: str) -> tuple[float, float] | None:
    params = {"q": f"{city}, India", "limit": 1, "lang": "en"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"{PHOTON_BASE_URL}/api", params=params, headers=TRAVEL_HEADERS)
        if response.status_code >= 400:
            return None
        payload = response.json()

    features = payload.get("features") if isinstance(payload, dict) else None
    feature = features[0] if isinstance(features, list) and features and isinstance(features[0], dict) else None
    geometry = feature.get("geometry") if isinstance(feature, dict) and isinstance(feature.get("geometry"), dict) else None
    coordinates = geometry.get("coordinates") if isinstance(geometry, dict) and isinstance(geometry.get("coordinates"), list) else None
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    lon, lat = coordinates[0], coordinates[1]
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    return float(lat), float(lon)


async def _ors_duration_minutes(
    *,
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    profile: str,
) -> dict[str, Any]:
    if not OPENROUTESERVICE_API_KEY:
        distance_km = _haversine_km(origin_lat, origin_lng, destination_lat, destination_lng)
        fallback_speed = 5.0 if profile == OPENROUTESERVICE_WALKING_PROFILE else 22.0
        if profile == OPENROUTESERVICE_BUS_PROFILE:
            fallback_speed = 30.0
        elif profile == OPENROUTESERVICE_METRO_PROFILE:
            fallback_speed = 34.0
        minutes = max(1, int(round((distance_km / fallback_speed) * 60.0)))
        return {
            "minutes": minutes,
            "distance_meters": int(round(distance_km * 1000.0)),
            "profile": profile,
            "source": "deterministic_fallback",
        }

    headers = {"Authorization": OPENROUTESERVICE_API_KEY, **TRAVEL_HEADERS}
    body = {"coordinates": [[origin_lng, origin_lat], [destination_lng, destination_lat]]}
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.post(
            f"{OPENROUTESERVICE_BASE_URL}/v2/directions/{profile}/geojson",
            headers=headers,
            json=body,
        )
        if response.status_code >= 400:
            return {"minutes": None, "distance_meters": None, "profile": profile, "source": "openrouteservice"}
        payload = response.json()

    features = payload.get("features") if isinstance(payload, dict) else None
    feature = features[0] if isinstance(features, list) and features and isinstance(features[0], dict) else None
    properties = feature.get("properties") if isinstance(feature, dict) and isinstance(feature.get("properties"), dict) else {}
    summary = properties.get("summary") if isinstance(properties, dict) and isinstance(properties.get("summary"), dict) else {}
    duration_seconds = summary.get("duration") if isinstance(summary, dict) else None
    distance_meters = summary.get("distance") if isinstance(summary, dict) else None
    minutes = int(round(float(duration_seconds) / 60.0)) if isinstance(duration_seconds, (int, float)) else None

    return {
        "minutes": minutes,
        "distance_meters": int(distance_meters) if isinstance(distance_meters, (int, float)) else None,
        "profile": profile,
        "source": "openrouteservice",
    }


def _extract_rail_rows(payload: dict[str, Any], origin_city: str, destination_city: str, journey_date: str, limit: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for key in ("trains", "results", "data", "schedules"):
        rows = payload.get(key)
        if isinstance(rows, list):
            candidates.extend([item for item in rows if isinstance(item, dict)])
        elif isinstance(rows, dict):
            candidates.append(rows)

    normalized: list[dict[str, Any]] = []
    for item in candidates:
        duration_minutes = item.get("duration_minutes")
        if duration_minutes is None and isinstance(item.get("duration"), (int, float)):
            duration_minutes = int(item["duration"])
        elif duration_minutes is None and isinstance(item.get("duration"), str) and ":" in item["duration"]:
            parts = item["duration"].split(":")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                duration_minutes = int(parts[0]) * 60 + int(parts[1])

        normalized.append(
            {
                "train_name": item.get("train_name") or item.get("name") or item.get("train") or "Indian Railways service",
                "train_number": item.get("train_number") or item.get("number") or item.get("train_no"),
                "origin_city": origin_city,
                "destination_city": destination_city,
                "journey_date": journey_date,
                "departure": item.get("departure") or item.get("departure_time") or item.get("depart_at"),
                "arrival": item.get("arrival") or item.get("arrival_time") or item.get("arrive_at"),
                "duration_minutes": int(duration_minutes) if isinstance(duration_minutes, (int, float)) else None,
                "stops": item.get("stops") if isinstance(item.get("stops"), int) else item.get("transfers"),
                "price_inr": item.get("price_inr") if isinstance(item.get("price_inr"), (int, float)) else item.get("price"),
                "currency": item.get("currency") or "INR",
                "booking_url": item.get("booking_url") or item.get("link") or item.get("url"),
                "source": "railapi",
            }
        )

    normalized.sort(
        key=lambda row: (
            row.get("duration_minutes") is None,
            row.get("duration_minutes") or 10**9,
            row.get("price_inr") or 10**9,
        )
    )
    return normalized[: max(1, min(limit, 20))]


@mcp.tool()
async def search_trains(
    origin_city: str,
    destination_city: str,
    journey_date: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    journey_date = _resolve_date(journey_date, default_days=14)
    resolved_limit = max(1, min(int(limit), 20))

    if not INDIAN_RAILWAYS_BASE_URL:
        origin_coords = await _resolve_city_coordinates(origin_city)
        destination_coords = await _resolve_city_coordinates(destination_city)
        distance_km = None
        if origin_coords and destination_coords:
            distance_km = _haversine_km(origin_coords[0], origin_coords[1], destination_coords[0], destination_coords[1])
        estimated_minutes = None
        if distance_km is not None:
            estimated_minutes = max(60, int(round((distance_km / 70.0) * 60.0)))
        return [
            {
                "train_name": f"{origin_city}-{destination_city} express",
                "train_number": "FALLBACK-RAIL",
                "origin_city": origin_city,
                "destination_city": destination_city,
                "journey_date": journey_date,
                "departure": f"{journey_date}T07:00:00",
                "arrival": f"{journey_date}T{(7 + max(1, (estimated_minutes or 360) // 60)) % 24:02d}:30:00",
                "duration_minutes": estimated_minutes or 360,
                "stops": 0,
                "price_inr": 0.0,
                "currency": "INR",
                "booking_url": None,
                "source": "deterministic_fallback",
            }
        ][:resolved_limit]

    params = {"origin": origin_city, "destination": destination_city, "journey_date": journey_date, "limit": resolved_limit}
    headers = {"Accept": "application/json", **TRAVEL_HEADERS}
    if INDIAN_RAILWAYS_API_KEY:
        headers["Authorization"] = f"Bearer {INDIAN_RAILWAYS_API_KEY}"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{INDIAN_RAILWAYS_BASE_URL}/search", params=params, headers=headers)
        if response.status_code >= 400:
            return await search_trains(origin_city=origin_city, destination_city=destination_city, journey_date=journey_date, limit=resolved_limit)
        payload = response.json()

    return _extract_rail_rows(payload if isinstance(payload, dict) else {}, origin_city, destination_city, journey_date, resolved_limit)


@mcp.tool()
async def search_buses(
    origin_city: str,
    destination_city: str,
    journey_date: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    journey_date = _resolve_date(journey_date, default_days=7)
    resolved_limit = max(1, min(int(limit), 10))
    origin_coords = await _resolve_city_coordinates(origin_city)
    destination_coords = await _resolve_city_coordinates(destination_city)
    if not origin_coords or not destination_coords:
        return [
            {
                "operator": "India intercity bus",
                "origin_city": origin_city,
                "destination_city": destination_city,
                "journey_date": journey_date,
                "departure": f"{journey_date}T08:00:00",
                "arrival": f"{journey_date}T13:30:00",
                "duration_minutes": 330,
                "price_inr": 600.0,
                "currency": "INR",
                "source": "deterministic_fallback",
            }
        ][:resolved_limit]

    route = await _ors_duration_minutes(
        origin_lat=origin_coords[0],
        origin_lng=origin_coords[1],
        destination_lat=destination_coords[0],
        destination_lng=destination_coords[1],
        profile=OPENROUTESERVICE_BUS_PROFILE,
    )
    minutes = route.get("minutes") or 360
    distance_km = _haversine_km(origin_coords[0], origin_coords[1], destination_coords[0], destination_coords[1])

    return [
        {
            "operator": "Intercity bus",
            "origin_city": origin_city,
            "destination_city": destination_city,
            "journey_date": journey_date,
            "departure": f"{journey_date}T08:00:00",
            "arrival": f"{journey_date}T{(8 + max(1, minutes // 60)) % 24:02d}:00:00",
            "duration_minutes": minutes,
            "distance_km": round(distance_km, 2),
            "price_inr": round(max(150.0, distance_km * 4.5), 2),
            "currency": "INR",
            "route_profile": route.get("profile"),
            "source": route.get("source"),
        }
    ][:resolved_limit]


@mcp.tool()
async def search_metro(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    city: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    route = await _ors_duration_minutes(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        destination_lat=destination_lat,
        destination_lng=destination_lng,
        profile=OPENROUTESERVICE_METRO_PROFILE,
    )
    distance_km = _haversine_km(origin_lat, origin_lng, destination_lat, destination_lng)
    minutes = route.get("minutes") or max(5, int(round(distance_km * 2.2)))
    resolved_limit = max(1, min(int(limit), 10))

    return [
        {
            "city": city,
            "mode": "metro",
            "origin": {"latitude": origin_lat, "longitude": origin_lng},
            "destination": {"latitude": destination_lat, "longitude": destination_lng},
            "distance_km": round(distance_km, 2),
            "duration_minutes": minutes,
            "price_inr": round(max(20.0, distance_km * 8.0), 2),
            "currency": "INR",
            "route_profile": route.get("profile"),
            "source": route.get("source"),
        }
    ][:resolved_limit]


@mcp.tool()
async def get_city_spots(city: str, max_results: int = 10) -> list[dict[str, Any]]:
    params = {"q": f"coworking library cafe in {city}", "limit": max(1, min(max_results, 30)), "lang": "en"}
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.get(f"{PHOTON_BASE_URL}/api", params=params, headers=TRAVEL_HEADERS)
        if response.status_code >= 400:
            return []
        payload = response.json()

    features = payload.get("features") if isinstance(payload, dict) else None
    if not isinstance(features, list):
        return []

    result: list[dict[str, Any]] = []
    for row in features:
        if not isinstance(row, dict):
            continue
        props = row.get("properties") if isinstance(row.get("properties"), dict) else {}
        geometry = row.get("geometry") if isinstance(row.get("geometry"), dict) else {}
        coords = geometry.get("coordinates") if isinstance(geometry.get("coordinates"), list) else [None, None]
        result.append({"name": props.get("name") or "Unknown spot", "address": props.get("street") or props.get("city") or city, "latitude": coords[1], "longitude": coords[0], "category": props.get("osm_value") or "place"})
    return result[: max_results]


@mcp.tool()
async def get_nearby_spots(
    latitude: float,
    longitude: float,
    radius_meters: int = 1500,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    del radius_meters
    params = {"q": "coworking library cafe", "lat": latitude, "lon": longitude, "limit": max(1, min(max_results, 20))}
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.get(f"{PHOTON_BASE_URL}/api", params=params, headers=TRAVEL_HEADERS)
        if response.status_code >= 400:
            return []
        payload = response.json()

    features = payload.get("features") if isinstance(payload, dict) else None
    if not isinstance(features, list):
        return []

    result: list[dict[str, Any]] = []
    for row in features:
        if not isinstance(row, dict):
            continue
        props = row.get("properties") if isinstance(row.get("properties"), dict) else {}
        geometry = row.get("geometry") if isinstance(row.get("geometry"), dict) else {}
        coords = geometry.get("coordinates") if isinstance(geometry.get("coordinates"), list) else [None, None]
        result.append({"name": props.get("name") or "Unknown spot", "address": props.get("street") or props.get("city"), "latitude": coords[1], "longitude": coords[0], "category": props.get("osm_value") or "place"})
    return result[: max_results]


@mcp.tool()
async def calculate_transit_duration(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    mode: str = "walking",
) -> dict[str, Any]:
    profile_map = {
        "passenger_train": OPENROUTESERVICE_BUS_PROFILE,
        "train": OPENROUTESERVICE_BUS_PROFILE,
        "bus": OPENROUTESERVICE_BUS_PROFILE,
        "metro": OPENROUTESERVICE_METRO_PROFILE,
        "walking": OPENROUTESERVICE_WALKING_PROFILE,
    }
    profile = profile_map.get((mode or "walking").lower(), OPENROUTESERVICE_WALKING_PROFILE)
    return await _ors_duration_minutes(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        destination_lat=destination_lat,
        destination_lng=destination_lng,
        profile=profile,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")