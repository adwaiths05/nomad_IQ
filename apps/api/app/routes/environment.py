from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.environment import EnvironmentEvaluateRequest, EnvironmentRead
from app.services.environment_service import evaluate_environment, get_environment

router = APIRouter(tags=["environment"])


@router.post("/environment/evaluate", response_model=EnvironmentRead)
async def evaluate_environment_endpoint(payload: EnvironmentEvaluateRequest, db: AsyncSession = Depends(get_db)) -> EnvironmentRead:
    row = await evaluate_environment(
        db,
        str(payload.trip_id),
        route_distance_km=payload.route_distance_km,
        transit_mode=payload.transit_mode,
    )
    return EnvironmentRead.model_validate(row)


@router.get("/trips/{trip_id}/environment", response_model=EnvironmentRead)
async def get_environment_endpoint(trip_id: UUID, db: AsyncSession = Depends(get_db)) -> EnvironmentRead:
    row = await get_environment(db, str(trip_id))
    return EnvironmentRead.model_validate(row)
