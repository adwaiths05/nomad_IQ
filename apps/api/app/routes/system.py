from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pipeline import run_plan_trip, run_replan_trip
from app.dependencies.db import get_db
from app.schemas.trip import PlanTripRequest, ReplanTripRequest
from app.services.explain_service import create_stub_explanation
from app.services.trip_service import get_trip

router = APIRouter(tags=["system"])


@router.post("/plan-trip")
async def plan_trip(payload: PlanTripRequest, db: AsyncSession = Depends(get_db)) -> dict:
    trip = await get_trip(db, str(payload.trip_id))
    plan = await run_plan_trip(db, trip)
    await create_stub_explanation(db, str(trip.id), None, "plan_trip")
    return {"trip_id": str(trip.id), "plan": plan}


@router.post("/trips/{trip_id}/replan")
async def replan_trip(trip_id: UUID, payload: ReplanTripRequest, db: AsyncSession = Depends(get_db)) -> dict:
    trip = await get_trip(db, str(trip_id))
    old_plan = {"city": trip.city, "status": trip.status}
    plan = await run_replan_trip(db, trip, payload.reason, old_plan)
    await create_stub_explanation(db, str(trip.id), None, "replan")
    return {"trip_id": str(trip.id), "plan": plan}
