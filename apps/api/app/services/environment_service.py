from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.environment import EnvironmentalScore
from app.models.trip import Trip


async def evaluate_environment(db: AsyncSession, trip_id: str) -> EnvironmentalScore:
    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    score = EnvironmentalScore(
        trip_id=trip_id,
        transport_score=7.8,
        distance_score=7.4,
        crowd_pressure=6.9,
        total_score=7.37,
        suggestions={"transport": "Prefer metro and walking loops", "timing": "Visit hotspots early morning"},
    )
    db.add(score)
    await db.commit()
    await db.refresh(score)
    return score


async def get_environment(db: AsyncSession, trip_id: str) -> EnvironmentalScore:
    env = await db.scalar(select(EnvironmentalScore).where(EnvironmentalScore.trip_id == trip_id))
    if env is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment score not found")
    return env
