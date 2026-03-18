from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip
from app.schemas.trip import TripCreate, TripPatch


async def create_trip(db: AsyncSession, payload: TripCreate) -> Trip:
    trip = Trip(**payload.model_dump(), status="draft")
    db.add(trip)
    await db.commit()
    await db.refresh(trip)
    return trip


async def get_trip(db: AsyncSession, trip_id: str) -> Trip:
    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


async def list_trips(db: AsyncSession) -> list[Trip]:
    rows = await db.scalars(select(Trip).order_by(Trip.start_date.desc()))
    return list(rows)


async def patch_trip(db: AsyncSession, trip_id: str, payload: TripPatch) -> Trip:
    trip = await get_trip(db, trip_id)
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(trip, key, value)
    await db.commit()
    await db.refresh(trip)
    return trip
