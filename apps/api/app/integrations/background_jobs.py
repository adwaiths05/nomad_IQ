import asyncio
from datetime import datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.integrations.cache import cache_set_json
from app.integrations.external_apis import fetch_numbeo_city_baseline
from app.models.cost_of_living import CityCostBaseline
from app.models.trip import Trip


async def refresh_numbeo_baselines_once() -> None:
    async with SessionLocal() as db:
        cities = set(await db.scalars(select(Trip.city)))
        for city in cities:
            baseline = await fetch_numbeo_city_baseline(str(city))
            if baseline is None:
                continue

            existing = await db.scalar(select(CityCostBaseline).where(CityCostBaseline.city == str(city)))
            if existing is None:
                existing = CityCostBaseline(city=str(city))
                db.add(existing)

            existing.currency = str(baseline["currency"])
            existing.daily_food = float(baseline["daily_food"])
            existing.daily_transport = float(baseline["daily_transport"])
            existing.daily_lodging = float(baseline["daily_lodging"])
            existing.daily_activities = float(baseline["daily_activities"])
            existing.source = str(baseline["source"])
            existing.raw_payload = baseline["raw"]
            existing.updated_at = datetime.utcnow()

        await db.commit()


async def numbeo_refresh_loop() -> None:
    while True:
        await refresh_numbeo_baselines_once()
        await asyncio.sleep(30 * 24 * 60 * 60)
