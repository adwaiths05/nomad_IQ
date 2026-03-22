import asyncio

from fastapi import FastAPI

from app.config.settings import get_settings
from app.db.init_db import init_db
from app.integrations.background_jobs import exchange_rate_refresh_loop, numbeo_refresh_loop
from app.routes import (
    auth,
    budget,
    environment,
    events,
    explain,
    groups,
    integrations,
    itinerary,
    memory,
    places,
    profiles,
    scoring,
    system,
    trips,
    users,
    weather,
)

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.app_debug)
_background_tasks: list[asyncio.Task] = []

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(groups.router)
app.include_router(profiles.router)
app.include_router(memory.router)
app.include_router(places.router)
app.include_router(events.router)
app.include_router(trips.router)
app.include_router(system.router)
app.include_router(itinerary.router)
app.include_router(scoring.router)
app.include_router(budget.router)
app.include_router(weather.router)
app.include_router(environment.router)
app.include_router(explain.router)
app.include_router(integrations.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event() -> None:
    await init_db()
    _background_tasks.append(asyncio.create_task(exchange_rate_refresh_loop()))
    _background_tasks.append(asyncio.create_task(numbeo_refresh_loop()))


@app.on_event("shutdown")
async def shutdown_event() -> None:
    for task in _background_tasks:
        task.cancel()
