import os
from datetime import date, timedelta
from typing import Any

import httpx
from fastmcp import FastMCP


mcp = FastMCP("Nomad-IQ-Kiwi")

TEQUILA_API_KEY = os.environ.get("TEQUILA_API_KEY", "").strip()
TEQUILA_BASE_URL = os.environ.get("TEQUILA_BASE_URL", "https://tequila-api.kiwi.com").rstrip("/")


def _require_api_key() -> str:
    if not TEQUILA_API_KEY:
        raise RuntimeError("TEQUILA_API_KEY environment variable is required")
    return TEQUILA_API_KEY


def _resolve_date_window(start_date: str | None, end_date: str | None) -> tuple[str, str]:
    today = date.today()

    if isinstance(start_date, str) and start_date.strip():
        resolved_start = date.fromisoformat(start_date[:10])
    else:
        resolved_start = today

    if isinstance(end_date, str) and end_date.strip():
        resolved_end = date.fromisoformat(end_date[:10])
    else:
        resolved_end = resolved_start + timedelta(days=30)

    if resolved_end < resolved_start:
        resolved_end = resolved_start

    return resolved_start.isoformat(), resolved_end.isoformat()


def _clean_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None and value != ""}


async def _api_get(path: str, params: dict[str, Any]) -> dict[str, Any] | list[Any]:
    headers = {
        "Content-Type": "application/json",
        "apikey": _require_api_key(),
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.get(f"{TEQUILA_BASE_URL}/{path.lstrip('/')}", headers=headers, params=_clean_params(params))
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def search_flights(
    city: str,
    start_date: str | None = None,
    end_date: str | None = None,
    origin_city: str | None = None,
    limit: int = 10,
    currency: str = "USD",
) -> dict[str, Any]:
    """
    Search live flight options using the Tequila search endpoint.
    """
    date_from, date_to = _resolve_date_window(start_date, end_date)
    payload = await _api_get(
        "/v2/search",
        {
            "fly_from": origin_city or "anywhere",
            "fly_to": city,
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit,
            "curr": currency.upper(),
            "sort": "price",
            "one_for_city": 1,
        },
    )
    return payload if isinstance(payload, dict) else {"data": payload}


@mcp.tool()
async def search_nomad_flights(
    origin_city: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    nights_in_dst_from: int | None = None,
    nights_in_dst_to: int | None = None,
    max_fly_duration: int | None = None,
    limit: int = 10,
    currency: str = "USD",
) -> dict[str, Any]:
    """
    Search flexible multi-city deals through Tequila's Nomad endpoint.
    """
    date_from, date_to = _resolve_date_window(start_date, end_date)
    payload = await _api_get(
        "/v2/nomad",
        {
            "fly_from": origin_city or "anywhere",
            "date_from": date_from,
            "date_to": date_to,
            "nights_in_dst_from": nights_in_dst_from,
            "nights_in_dst_to": nights_in_dst_to,
            "max_fly_duration": max_fly_duration,
            "limit": limit,
            "curr": currency.upper(),
        },
    )
    return payload if isinstance(payload, dict) else {"data": payload}


if __name__ == "__main__":
    mcp.run(transport="stdio")