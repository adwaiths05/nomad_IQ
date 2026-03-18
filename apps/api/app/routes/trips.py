from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.trip import TripCreate, TripPatch, TripRead
from app.services.trip_service import create_trip, get_trip, list_trips, patch_trip

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("", response_model=TripRead)
async def create_trip_endpoint(payload: TripCreate, db: AsyncSession = Depends(get_db)) -> TripRead:
    row = await create_trip(db, payload)
    return TripRead.model_validate(row)


@router.get("/{trip_id}", response_model=TripRead)
async def get_trip_endpoint(trip_id: UUID, db: AsyncSession = Depends(get_db)) -> TripRead:
    row = await get_trip(db, str(trip_id))
    return TripRead.model_validate(row)


@router.get("", response_model=list[TripRead])
async def list_trips_endpoint(db: AsyncSession = Depends(get_db)) -> list[TripRead]:
    rows = await list_trips(db)
    return [TripRead.model_validate(row) for row in rows]


@router.patch("/{trip_id}", response_model=TripRead)
async def patch_trip_endpoint(trip_id: UUID, payload: TripPatch, db: AsyncSession = Depends(get_db)) -> TripRead:
    row = await patch_trip(db, str(trip_id), payload)
    return TripRead.model_validate(row)
