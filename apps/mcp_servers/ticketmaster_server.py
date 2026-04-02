import os
import httpx
from typing import Optional, Dict, Any, List
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Nomad-IQ-Ticketmaster")

# Configuration
API_KEY = os.environ.get("TICKETMASTER_API_KEY")
BASE_URL = "https://app.ticketmaster.com/discovery/v2"

async def make_request(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Helper to handle Ticketmaster API requests."""
    if not params:
        params = {}
    params["apikey"] = API_KEY
    
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/{endpoint}.json"
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def search_events(
    city: Optional[str] = None,
    keyword: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    size: int = 20,
    page: int = 0
) -> Dict[str, Any]:
    """
    Search for events on Ticketmaster using filters like city, date range, and keywords.
    Dates should be in ISO format (YYYY-MM-DDTHH:mm:ssZ).
    """
    params = {
        "city": city,
        "keyword": keyword,
        "startDateTime": start_date,
        "endDateTime": end_date,
        "size": size,
        "page": page
    }
    # Filter out None values
    params = {k: v for k, v in params.items() if v is not None}
    return await make_request("events", params)

@mcp.tool()
async def get_event_details(event_id: str) -> Dict[str, Any]:
    """Retrieve detailed information about a specific event by ID."""
    return await make_request(f"events/{event_id}")

@mcp.tool()
async def get_event_images(event_id: str) -> Dict[str, Any]:
    """Retrieve images and metadata for a specific event by ID."""
    data = await make_request(f"events/{event_id}")
    return {"images": data.get("images", [])}

@mcp.tool()
async def get_classifications(locale: str = "en-us") -> Dict[str, Any]:
    """Retrieve the hierarchical taxonomy (Segments, Genres, Subgenres) for categorizing events."""
    return await make_request("classifications", {"locale": locale})

@mcp.tool()
async def get_segment_details(segment_id: str) -> Dict[str, Any]:
    """Retrieve detailed metadata for a segment, including all associated genres and subgenres."""
    return await make_request(f"classifications/segments/{segment_id}")

@mcp.tool()
async def get_genre_details(genre_id: str) -> Dict[str, Any]:
    """Retrieve detailed metadata for a specific genre."""
    return await make_request(f"classifications/genres/{genre_id}")

@mcp.tool()
async def get_subgenre_details(subgenre_id: str) -> Dict[str, Any]:
    """Retrieve metadata for a single subgenre by ID."""
    return await make_request(f"classifications/subgenres/{subgenre_id}")

@mcp.tool()
async def get_venues(keyword: Optional[str] = None, city: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve a list of venues based on name (keyword) or location."""
    params = {"keyword": keyword, "city": city}
    params = {k: v for k, v in params.items() if v is not None}
    return await make_request("venues", params)

@mcp.tool()
async def get_venue_details_enhanced(venue_id: str) -> Dict[str, Any]:
    """Retrieve comprehensive details about a venue including box office and social media data."""
    return await make_request(f"venues/{venue_id}")

@mcp.tool()
async def get_advanced_suggestions(keyword: str, latlong: Optional[str] = None) -> Dict[str, Any]:
    """Get auto-complete suggestions for attractions, venues, and events."""
    params = {"keyword": keyword, "latlong": latlong}
    params = {k: v for k, v in params.items() if v is not None}
    return await make_request("suggest", params)

if __name__ == "__main__":
    mcp.run(transport="stdio")