import os
from datetime import date, timedelta
from typing import Any

import httpx
from fastmcp import FastMCP


mcp = FastMCP("mcp-travel")

AMADEUS_CLIENT_ID = os.environ.get("AMADEUS_CLIENT_ID", "").strip()
AMADEUS_CLIENT_SECRET = os.environ.get("AMADEUS_CLIENT_SECRET", "").strip()
AMADEUS_BASE_URL = os.environ.get("AMADEUS_BASE_URL", "https://test.api.amadeus.com").rstrip("/")

PHOTON_BASE_URL = os.environ.get("PHOTON_BASE_URL", "https://photon.komoot.io").rstrip("/")
OSRM_BASE_URL = os.environ.get("OSRM_BASE_URL", "https://router.project-osrm.org").rstrip("/")
TRAVEL_HEADERS = {"User-Agent": "nomadiq-mcp-travel/1.0"}

AVIATIONSTACK_API_KEY = os.environ.get("AVIATIONSTACK_API_KEY", "").strip()
AVIATIONSTACK_BASE_URL = os.environ.get("AVIATIONSTACK_BASE_URL", "https://api.aviationstack.com/v1").rstrip("/")
OPENSKY_BASE_URL = os.environ.get("OPENSKY_BASE_URL", "https://opensky-network.org/api").rstrip("/")


async def _get_amadeus_token() -> str | None:
    if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
        return None
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{AMADEUS_BASE_URL}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": AMADEUS_CLIENT_ID,
                "client_secret": AMADEUS_CLIENT_SECRET,
            },
        )
        response.raise_for_status()
        body = response.json()
        return str(body.get("access_token") or "") or None


def _resolve_date(value: str | None, default_days: int) -> str:
    if value:
        return value[:10]
    return (date.today() + timedelta(days=default_days)).isoformat()


async def _resolve_iata(keyword: str, token: str) -> str | None:
    cleaned = (keyword or "").strip().upper()
    if len(cleaned) == 3 and cleaned.isalpha():
        return cleaned

    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "subType": "CITY,AIRPORT",
        "keyword": keyword,
        "page[limit]": 1,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"{AMADEUS_BASE_URL}/v1/reference-data/locations",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        payload = response.json()

    rows = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(rows, list) and rows:
        top = rows[0] if isinstance(rows[0], dict) else {}
        iata = top.get("iataCode")
        if isinstance(iata, str) and iata:
            return iata
    return None


@mcp.tool()
async def search_flights(
    city: str,
    start_date: str | None = None,
    end_date: str | None = None,
    origin_city: str | None = None,
    limit: int = 10,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    token = await _get_amadeus_token()
    if not token:
        return []

    origin = await _resolve_iata(origin_city or "NYC", token)
    destination = await _resolve_iata(city, token)
    if not origin or not destination:
        return []

    departure_date = _resolve_date(start_date, default_days=14)
    return_date = _resolve_date(end_date, default_days=21)

    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "returnDate": return_date,
        "adults": 1,
        "max": max(1, min(int(limit), 50)),
        "currencyCode": currency.upper(),
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers",
            headers=headers,
            params=params,
        )
        if response.status_code >= 400:
            return []
        payload = response.json()

    offers = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(offers, list):
        return []

    result: list[dict[str, Any]] = []
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        itineraries = offer.get("itineraries") if isinstance(offer.get("itineraries"), list) else []
        first = itineraries[0] if itineraries and isinstance(itineraries[0], dict) else {}
        segments = first.get("segments") if isinstance(first.get("segments"), list) else []
        first_seg = segments[0] if segments and isinstance(segments[0], dict) else {}
        last_seg = segments[-1] if segments and isinstance(segments[-1], dict) else {}
        price_block = offer.get("price") if isinstance(offer.get("price"), dict) else {}

        result.append(
            {
                "airline": str((offer.get("validatingAirlineCodes") or ["Unknown"])[0]),
                "origin": origin,
                "destination": destination,
                "departure": first_seg.get("departure", {}).get("at") if isinstance(first_seg.get("departure"), dict) else None,
                "arrival": last_seg.get("arrival", {}).get("at") if isinstance(last_seg.get("arrival"), dict) else None,
                "duration": first.get("duration"),
                "stops": max(len(segments) - 1, 0),
                "price": float(price_block.get("grandTotal", 0)) if str(price_block.get("grandTotal", "")).strip() else None,
                "currency": price_block.get("currency") or currency.upper(),
            }
        )

    return result


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
