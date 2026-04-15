from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.engines.itinerary_optimizer import optimize_itinerary
from app.integrations.cache import cache_get_json, cache_set_json
from app.integrations.external_apis import MapsClient, MapsRoutesClient
from app.models.place import Place
from app.models.profile import TravelerProfile
from app.models.trip import Trip
from app.schemas.itinerary import ItineraryItemRead, ItineraryItemUpdate, ItineraryOptimizeRequest
from app.services.itinerary_service import get_trip_itinerary, update_item

router = APIRouter(tags=["itinerary"])


@router.get("/trips/{trip_id}/itinerary")
async def get_itinerary(trip_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    data = await get_trip_itinerary(db, str(trip_id))
    return {
        "days": data["days"],
        "items": [ItineraryItemRead.model_validate(row).model_dump() for row in data["items"]],
    }


@router.put("/itinerary/items/{item_id}", response_model=ItineraryItemRead)
async def update_itinerary_item(item_id: UUID, payload: ItineraryItemUpdate, db: AsyncSession = Depends(get_db)) -> ItineraryItemRead:
    row = await update_item(db, str(item_id), payload)
    return ItineraryItemRead.model_validate(row)


@router.post("/itinerary/optimize")
async def optimize_itinerary_endpoint(payload: ItineraryOptimizeRequest, db: AsyncSession = Depends(get_db)) -> dict:
    data = await get_trip_itinerary(db, str(payload.trip_id))
    items = [ItineraryItemRead.model_validate(row).model_dump() for row in data["items"]]

    resolved_work_start = payload.work_start
    resolved_work_end = payload.work_end
    if payload.remote_work_mode and (resolved_work_start is None or resolved_work_end is None):
        trip = await db.get(Trip, str(payload.trip_id))
        if trip is not None:
            profile = await db.scalar(
                select(TravelerProfile).where(TravelerProfile.user_id == trip.user_id).order_by(TravelerProfile.id.desc())
            )
            if profile and profile.remote_work_mode:
                resolved_work_start = resolved_work_start or profile.work_start
                resolved_work_end = resolved_work_end or profile.work_end

    if payload.remote_work_mode and resolved_work_start and resolved_work_end and payload.latitude is not None and payload.longitude is not None:
        cache_key = (
            f"maps:work:{payload.latitude:.4f}:{payload.longitude:.4f}:"
            f"{resolved_work_start.isoformat()}:{resolved_work_end.isoformat()}"
        )
        cached = await cache_get_json(cache_key)
        if isinstance(cached, list):
            spots = cached
            source_type = "cached_api"
        else:
            spots = await MapsClient().nearby_productive_spots(payload.latitude, payload.longitude)
            await cache_set_json(cache_key, spots, ttl_seconds=30 * 24 * 60 * 60)
            source_type = "mcp_maps"

        for spot in spots[:2]:
            items.append(
                {
                    "id": None,
                    "day_id": None,
                    "place_id": None,
                    "start_time": resolved_work_start,
                    "end_time": resolved_work_end,
                    "activity_type": f"Remote work at {spot.get('name', 'productive spot')}",
                    "travel_time_minutes": 0,
                    "cost_estimate": 0,
                    "confidence_score": "high" if source_type == "mcp_maps" else "medium",
                    "source_type": source_type,
                }
            )

    optimized_items = optimize_itinerary(items, flexibility_level=payload.flexibility_level)

    place_ids = [item.get("place_id") for item in optimized_items if item.get("place_id")]
    place_map: dict[str, Place] = {}
    if place_ids:
        place_rows = await db.scalars(select(Place).where(Place.id.in_(place_ids)))
        place_map = {str(row.id): row for row in list(place_rows)}

    for idx in range(1, len(optimized_items)):
        prev = optimized_items[idx - 1]
        current = optimized_items[idx]
        prev_place = place_map.get(str(prev.get("place_id"))) if prev.get("place_id") else None
        current_place = place_map.get(str(current.get("place_id"))) if current.get("place_id") else None
        if prev_place is None or current_place is None:
            continue

        route_key = (
            f"routes:{prev_place.latitude:.4f}:{prev_place.longitude:.4f}:"
            f"{current_place.latitude:.4f}:{current_place.longitude:.4f}:transit"
        )
        cached = await cache_get_json(route_key)
        minutes = None
        if isinstance(cached, dict) and isinstance(cached.get("minutes"), int):
            minutes = int(cached["minutes"])
        else:
            minutes = await MapsRoutesClient().transit_duration_minutes(
                origin_lat=float(prev_place.latitude),
                origin_lng=float(prev_place.longitude),
                destination_lat=float(current_place.latitude),
                destination_lng=float(current_place.longitude),
            )
            if minutes is not None:
                await cache_set_json(route_key, {"minutes": minutes}, ttl_seconds=12 * 60 * 60)

        if minutes is not None:
            current["travel_time_minutes"] = minutes

    return {
        "trip_id": str(payload.trip_id),
        "optimized_items": optimized_items,
    }
