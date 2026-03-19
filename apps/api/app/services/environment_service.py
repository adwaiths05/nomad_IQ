from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.cache import cache_get_json, cache_set_json
from app.integrations.external_apis import ClimatiqClient
from app.models.environment import EnvironmentalScore
from app.models.trip import Trip


async def evaluate_environment(
    db: AsyncSession,
    trip_id: str,
    route_distance_km: float | None = None,
    transit_mode: str = "passenger_train",
) -> EnvironmentalScore:
    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    co2 = None
    if route_distance_km is not None and route_distance_km > 0:
        cache_key = f"climatiq:{transit_mode}:{route_distance_km:.2f}"
        cached = await cache_get_json(cache_key)
        payload = cached if isinstance(cached, dict) else None
        source = "cached_api" if payload else "fallback"
        if payload is None:
            payload = await ClimatiqClient().estimate_route_emissions(route_distance_km, mode=transit_mode)
            if payload:
                await cache_set_json(cache_key, payload, ttl_seconds=None)
                source = "climatiq"
        if payload:
            co2 = payload.get("co2e")

    score = EnvironmentalScore(
        trip_id=trip_id,
        transport_score=7.8,
        distance_score=7.4,
        crowd_pressure=6.9,
        total_score=7.37,
        suggestions={
            "transport": "Prefer metro and walking loops",
            "timing": "Visit hotspots early morning",
            "co2e_estimate": co2,
        },
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
