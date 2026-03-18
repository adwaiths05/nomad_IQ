from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.engines.itinerary_optimizer import optimize_itinerary
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
    return {"trip_id": str(payload.trip_id), "optimized_items": optimize_itinerary(items)}
