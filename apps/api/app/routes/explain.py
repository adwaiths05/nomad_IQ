from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.explain import ExplanationRead
from app.services.explain_service import get_item_explanation, list_trip_explanations

router = APIRouter(tags=["explainability"])


@router.get("/trips/{trip_id}/explanations", response_model=list[ExplanationRead])
async def get_trip_explanations(trip_id: UUID, db: AsyncSession = Depends(get_db)) -> list[ExplanationRead]:
    rows = await list_trip_explanations(db, str(trip_id))
    return [ExplanationRead.model_validate(row) for row in rows]


@router.get("/itinerary/items/{item_id}/explanation", response_model=ExplanationRead)
async def get_itinerary_explanation(item_id: UUID, db: AsyncSession = Depends(get_db)) -> ExplanationRead:
    row = await get_item_explanation(db, str(item_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Explanation not found")
    return ExplanationRead.model_validate(row)
