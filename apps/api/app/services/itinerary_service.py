from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.itinerary import ItineraryDay, ItineraryItem
from app.schemas.itinerary import ItineraryItemUpdate


async def get_trip_itinerary(db: AsyncSession, trip_id: str) -> dict[str, list]:
    days = list(await db.scalars(select(ItineraryDay).where(ItineraryDay.trip_id == trip_id).order_by(ItineraryDay.day_number.asc())))
    day_ids = [d.id for d in days]
    items = []
    if day_ids:
        items = list(await db.scalars(select(ItineraryItem).where(ItineraryItem.day_id.in_(day_ids))))
    return {"days": days, "items": items}


async def update_item(db: AsyncSession, item_id: str, payload: ItineraryItemUpdate) -> ItineraryItem:
    item = await db.get(ItineraryItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary item not found")

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item)
    return item
