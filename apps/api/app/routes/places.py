from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.place import PlaceRead, PlaceSearchRequest
from app.services.place_service import get_place, list_places, search_places

router = APIRouter(prefix="/places", tags=["places"])


@router.get("", response_model=list[PlaceRead])
async def get_places(db: AsyncSession = Depends(get_db)) -> list[PlaceRead]:
    rows = await list_places(db)
    return [PlaceRead.model_validate(row) for row in rows]


@router.get("/{place_id}", response_model=PlaceRead)
async def get_place_by_id(place_id: UUID, db: AsyncSession = Depends(get_db)) -> PlaceRead:
    row = await get_place(db, str(place_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    return PlaceRead.model_validate(row)


@router.post("/search", response_model=list[PlaceRead])
async def search_places_endpoint(payload: PlaceSearchRequest, db: AsyncSession = Depends(get_db)) -> list[PlaceRead]:
    rows = await search_places(db, payload.city, payload.category)
    return [PlaceRead.model_validate(row) for row in rows]
