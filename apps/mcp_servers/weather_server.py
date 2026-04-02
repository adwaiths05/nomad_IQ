import os
import httpx
from typing import Optional
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Nomad-IQ-Weather")

# Configuration
API_KEY = os.environ.get("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5"
GEO_URL = "http://api.openweathermap.org/geo/1.0"

async def make_request(url: str, params: dict):
    params["appid"] = API_KEY
    params["units"] = "metric"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_five_day_forecast(city: str) -> dict:
    """
    Get 5-day forecast every 3 hours. Required for Nomad IQ weather service.
    """
    # This matches the 'list' and 'pop' keys expected by weather_service.py
    return await make_request(f"{BASE_URL}/forecast", {"q": city})

@mcp.tool()
async def get_current_weather(q: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> dict:
    """
    Retrieve current weather data for a location. Provide 'q' (city name) OR 'lat' and 'lon'.
    """
    params = {"q": q} if q else {"lat": lat, "lon": lon}
    return await make_request(f"{BASE_URL}/weather", params)

@mcp.tool()
async def get_current_air_pollution(lat: float, lon: float) -> dict:
    """
    Fetch current air pollution data (CO, NO, NO2, O3, etc.) by coordinates.
    """
    return await make_request(f"{BASE_URL}/air_pollution", {"lat": lat, "lon": lon})

@mcp.tool()
async def get_air_pollution_forecast(lat: float, lon: float) -> dict:
    """
    Get forecasted air pollution data for a specific location.
    """
    return await make_request(f"{BASE_URL}/air_pollution/forecast", {"lat": lat, "lon": lon})

@mcp.tool()
async def get_direct_geocoding(name: str, limit: int = 1) -> list:
    """
    Convert a location name into geographic coordinates (lat/lon).
    """
    return await make_request(f"{GEO_URL}/direct", {"q": name, "limit": limit})

@mcp.tool()
async def get_reverse_geocoding(lat: float, lon: float, limit: int = 1) -> list:
    """
    Convert geographic coordinates into a location name.
    """
    return await make_request(f"{GEO_URL}/reverse", {"lat": lat, "lon": lon, "limit": limit})

if __name__ == "__main__":
    mcp.run(transport="stdio")