from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.event import EventRead
from app.services.event_service import get_event, list_events

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead])
async def get_events(db: AsyncSession = Depends(get_db)) -> list[EventRead]:
    rows = await list_events(db)
    return [EventRead.model_validate(row) for row in rows]


@router.get("/{event_id}", response_model=EventRead)
async def get_event_by_id(event_id: UUID, db: AsyncSession = Depends(get_db)) -> EventRead:
    row = await get_event(db, str(event_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return EventRead.model_validate(row)
