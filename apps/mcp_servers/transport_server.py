import os
from datetime import date, timedelta
from typing import Any

import httpx
from fastmcp import FastMCP


mcp = FastMCP("mcp-travel")

TRAVELPAYOUTS_API_TOKEN = os.environ.get("TRAVELPAYOUTS_API_TOKEN", "").strip()
TRAVELPAYOUTS_BASE_URL = os.environ.get("TRAVELPAYOUTS_BASE_URL", "https://api.travelpayouts.com/v1").rstrip("/")

PHOTON_BASE_URL = os.environ.get("PHOTON_BASE_URL", "https://photon.komoot.io").rstrip("/")
OSRM_BASE_URL = os.environ.get("OSRM_BASE_URL", "https://router.project-osrm.org").rstrip("/")
TRAVEL_HEADERS = {"User-Agent": "nomadiq-mcp-travel/1.0"}

AVIATIONSTACK_API_KEY = os.environ.get("AVIATIONSTACK_API_KEY", "").strip()
AVIATIONSTACK_BASE_URL = os.environ.get("AVIATIONSTACK_BASE_URL", "https://api.aviationstack.com/v1").rstrip("/")
OPENSKY_BASE_URL = os.environ.get("OPENSKY_BASE_URL", "https://opensky-network.org/api").rstrip("/")


CITY_TO_IATA = {
    "NEW YORK": "NYC",
    "LONDON": "LON",
    "PARIS": "PAR",
    "TOKYO": "TYO",
    "KOCHI": "COK",
    "DUBAI": "DXB",
    "BANGKOK": "BKK",
    "SINGAPORE": "SIN",
    "LISBON": "LIS",
    "MADRID": "MAD",
    "ROME": "ROM",
    "SEOUL": "SEL",
    "SYDNEY": "SYD",
    "TORONTO": "YTO",
}


def _resolve_date(value: str | None, default_days: int) -> str:
    if value:
        return value[:10]
    return (date.today() + timedelta(days=default_days)).isoformat()


def _resolve_iata(keyword: str | None) -> str | None:
    if not keyword:
        return None
    cleaned = (keyword or "").strip().upper()
    if len(cleaned) == 3 and cleaned.isalpha():
        return cleaned
    return CITY_TO_IATA.get(cleaned)


def _extract_travelpayouts_rows(payload: dict[str, Any], origin: str, destination: str, currency: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return rows

    # Handles both common TP payload shapes:
    # 1) data["LON"] -> {price, airline, flight_number, departure_at, return_at, ...}
    # 2) data["LON"] -> [{...}, {...}] or nested dict entries
    bucket = data.get(destination) if destination in data else None
    candidates: list[dict[str, Any]] = []

    if isinstance(bucket, dict) and isinstance(bucket.get("price"), (int, float)):
        candidates = [bucket]
    elif isinstance(bucket, dict):
        for val in bucket.values():
            if isinstance(val, dict):
                candidates.append(val)
            elif isinstance(val, list):
                candidates.extend([item for item in val if isinstance(item, dict)])
    elif isinstance(bucket, list):
        candidates = [item for item in bucket if isinstance(item, dict)]

    for item in candidates:
        raw_price = item.get("price")
        rows.append(
            {
                "airline": item.get("airline") or "Unknown",
                "origin": origin,
                "destination": destination,
                "departure": item.get("departure_at"),
                "arrival": item.get("return_at"),
                "duration": None,
                "stops": item.get("transfers") if isinstance(item.get("transfers"), int) else None,
                "price": float(raw_price) if isinstance(raw_price, (int, float)) else None,
                "currency": item.get("currency") or currency.upper(),
                "booking_url": item.get("link") or item.get("deep_link"),
                "flight_number": item.get("flight_number"),
                "source": "travelpayouts",
            }
        )
    return rows


@mcp.tool()
async def search_flights(
    city: str,
    start_date: str | None = None,
    end_date: str | None = None,
    origin_city: str | None = None,
    limit: int = 10,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    if not TRAVELPAYOUTS_API_TOKEN:
        return []

    origin = _resolve_iata(origin_city or "NYC")
    destination = _resolve_iata(city)
    if not origin or not destination:
        return []

    departure_date = _resolve_date(start_date, default_days=14)
    return_date = _resolve_date(end_date, default_days=21)

    params = {
        "token": TRAVELPAYOUTS_API_TOKEN,
        "origin": origin,
        "destination": destination,
        "depart_date": departure_date,
        "return_date": return_date,
        "currency": currency.upper(),
        "page": 1,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{TRAVELPAYOUTS_BASE_URL}/prices/cheap", params=params)
        if response.status_code >= 400:
            return []
        payload = response.json()

    result = _extract_travelpayouts_rows(payload if isinstance(payload, dict) else {}, origin, destination, currency)
    result.sort(key=lambda row: float(row.get("price") or 10**9))
    return result[: max(1, min(int(limit), 50))]


@mcp.tool()
async def search_nomad_deals(
    origin_city: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    nights_in_dst_from: int | None = None,
    nights_in_dst_to: int | None = None,
    max_fly_duration: int | None = None,
    limit: int = 10,
    currency: str = "USD",
) -> dict[str, Any]:
    del nights_in_dst_from, nights_in_dst_to, max_fly_duration
    origin = origin_city or "NYC"
    candidate_destinations = ["LON", "MAD", "LIS", "ROM", "BKK", "DXB"]

    all_offers: list[dict[str, Any]] = []
    for code in candidate_destinations:
        offers = await search_flights(
            city=code,
            start_date=start_date,
            end_date=end_date,
            origin_city=origin,
            limit=max(1, limit // 2),
            currency=currency,
        )
        all_offers.extend(offers)

    all_offers.sort(key=lambda row: float(row.get("price") or 10**9))
    return {
        "origin_city": origin,
        "currency": currency.upper(),
        "deals": all_offers[: max(1, limit)],
    }


@mcp.tool()
async def get_city_spots(city: str, max_results: int = 10) -> list[dict[str, Any]]:
    params = {
        "q": f"coworking library cafe in {city}",
        "limit": max(1, min(max_results, 30)),
        "lang": "en",
    }
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
        result.append(
            {
                "name": props.get("name") or "Unknown spot",
                "address": props.get("street") or props.get("city") or city,
                "latitude": coords[1],
                "longitude": coords[0],
                "category": props.get("osm_value") or "place",
            }
        )
    return result[: max_results]


@mcp.tool()
async def get_nearby_spots(
    latitude: float,
    longitude: float,
    radius_meters: int = 1500,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    del radius_meters
    params = {
        "q": "coworking library cafe",
        "lat": latitude,
        "lon": longitude,
        "limit": max(1, min(max_results, 20)),
    }
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
        result.append(
            {
                "name": props.get("name") or "Unknown spot",
                "address": props.get("street") or props.get("city"),
                "latitude": coords[1],
                "longitude": coords[0],
                "category": props.get("osm_value") or "place",
            }
        )
    return result[: max_results]


@mcp.tool()
async def calculate_transit_duration(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
) -> dict[str, Any]:
    coordinates = f"{origin_lng},{origin_lat};{destination_lng},{destination_lat}"
    params = {"overview": "false"}

    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.get(
            f"{OSRM_BASE_URL}/route/v1/driving/{coordinates}",
            params=params,
            headers=TRAVEL_HEADERS,
        )
        if response.status_code >= 400:
            return {"minutes": None, "source": "osrm"}
        payload = response.json()

    routes = payload.get("routes") if isinstance(payload, dict) else None
    top = routes[0] if isinstance(routes, list) and routes and isinstance(routes[0], dict) else {}
    duration_seconds = top.get("duration") if isinstance(top.get("duration"), (int, float)) else None
    minutes = int(round(float(duration_seconds) / 60)) if duration_seconds else None

    return {
        "minutes": minutes,
        "distance_meters": top.get("distance"),
        "source": "osrm",
    }


@mcp.tool()
async def get_flight_status(flight_iata: str) -> dict[str, Any]:
    if not AVIATIONSTACK_API_KEY:
        return {
            "flight_iata": flight_iata,
            "status": None,
            "source": "aviationstack_unconfigured",
        }

    params = {
        "access_key": AVIATIONSTACK_API_KEY,
        "flight_iata": flight_iata,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"{AVIATIONSTACK_BASE_URL}/flights", params=params)
        if response.status_code >= 400:
            return {
                "flight_iata": flight_iata,
                "status": None,
                "source": "aviationstack",
            }
        payload = response.json()

    rows = payload.get("data") if isinstance(payload, dict) else []
    top = rows[0] if isinstance(rows, list) and rows and isinstance(rows[0], dict) else {}
    flight = top.get("flight") if isinstance(top.get("flight"), dict) else {}
    departure = top.get("departure") if isinstance(top.get("departure"), dict) else {}
    arrival = top.get("arrival") if isinstance(top.get("arrival"), dict) else {}

    return {
        "flight_iata": flight.get("iata") or flight_iata,
        "status": top.get("flight_status"),
        "departure_airport": departure.get("airport"),
        "departure_scheduled": departure.get("scheduled"),
        "arrival_airport": arrival.get("airport"),
        "arrival_scheduled": arrival.get("scheduled"),
        "source": "aviationstack",
    }


@mcp.tool()
async def get_live_flights_bbox(
    lamin: float,
    lomin: float,
    lamax: float,
    lomax: float,
) -> dict[str, Any]:
    params = {
        "lamin": lamin,
        "lomin": lomin,
        "lamax": lamax,
        "lomax": lomax,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"{OPENSKY_BASE_URL}/states/all", params=params)
        if response.status_code >= 400:
            return {"count": 0, "states": [], "source": "opensky"}
        payload = response.json()

    states = payload.get("states") if isinstance(payload, dict) else None
    rows = states if isinstance(states, list) else []
    compact: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 9:
            continue
        compact.append(
            {
                "icao24": row[0],
                "callsign": row[1],
                "country": row[2],
                "longitude": row[5],
                "latitude": row[6],
                "altitude_m": row[7],
                "on_ground": row[8],
            }
        )

    return {
        "count": len(compact),
        "states": compact,
        "source": "opensky",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
