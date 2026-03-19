from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.engines.itinerary_optimizer import optimize_itinerary
from app.integrations.cache import cache_get_json, cache_set_json
from app.integrations.external_apis import GooglePlacesClient
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

    if payload.remote_work_mode and payload.work_start and payload.work_end and payload.latitude is not None and payload.longitude is not None:
        cache_key = (
            f"google_places:work:{payload.latitude:.4f}:{payload.longitude:.4f}:"
            f"{payload.work_start.isoformat()}:{payload.work_end.isoformat()}"
        )
        cached = await cache_get_json(cache_key)
        if isinstance(cached, list):
            spots = cached
            source_type = "cached_api"
        else:
            spots = await GooglePlacesClient().nearby_productive_spots(payload.latitude, payload.longitude)
            await cache_set_json(cache_key, spots, ttl_seconds=30 * 24 * 60 * 60)
            source_type = "google_places"

        for spot in spots[:2]:
            items.append(
                {
                    "id": None,
                    "day_id": None,
                    "place_id": None,
                    "start_time": payload.work_start,
                    "end_time": payload.work_end,
                    "activity_type": f"Remote work at {spot.get('name', 'productive spot')}",
                    "travel_time_minutes": 0,
                    "cost_estimate": 0,
                    "confidence_score": "high" if source_type == "google_places" else "medium",
                    "source_type": source_type,
                }
            )

    return {
        "trip_id": str(payload.trip_id),
        "optimized_items": optimize_itinerary(items, flexibility_level=payload.flexibility_level),
    }
