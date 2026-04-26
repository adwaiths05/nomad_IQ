import asyncio
import logging
from typing import Any

import httpx
from fastapi import FastAPI

from app.config.settings import get_settings
from app.db.init_db import init_db
from app.integrations.background_jobs import numbeo_refresh_loop
from app.routes import (
    ambient_ai,
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
logger = logging.getLogger(__name__)

app.include_router(auth.router)
app.include_router(ambient_ai.router)
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


async def _check_http_endpoint(client: httpx.AsyncClient, name: str, url: str) -> dict[str, Any]:
    try:
        response = await client.get(url)
        ok = response.status_code < 500
        return {
            "name": name,
            "url": url,
            "ok": ok,
            "status_code": response.status_code,
        }
    except httpx.HTTPError as exc:
        return {
            "name": name,
            "url": url,
            "ok": False,
            "error": str(exc),
        }


def _llm_models_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/models"
    return f"{base}/v1/models"


def _embeddings_health_urls(base_url: str) -> list[str]:
    base = base_url.rstrip("/")
    return [
        f"{base}/health",
        f"{base}/v1/health",
        f"{base}/",
    ]


@app.get("/health/startup")
async def startup_health_check() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=8) as client:
        checks.append(
            await _check_http_endpoint(
                client,
                "llm.models",
                _llm_models_url(settings.llm_base_url),
            )
        )

        embedding_result: dict[str, Any] | None = None
        for candidate in _embeddings_health_urls(settings.embeddings_base_url):
            current = await _check_http_endpoint(client, "embeddings.health", candidate)
            if current.get("ok"):
                embedding_result = current
                break
            if embedding_result is None:
                embedding_result = current
        if embedding_result is not None:
            checks.append(embedding_result)

        mcp_targets = [
            ("mcp.travel", settings.mcp_travel_url),
            ("mcp.rag", settings.mcp_rag_url),
        ]
        seen_urls: set[str] = set()
        for name, server_url in mcp_targets:
            if not server_url:
                checks.append({"name": name, "url": None, "ok": False, "error": "not_configured"})
                continue
            normalized = server_url.rstrip("/")
            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)
            checks.append(await _check_http_endpoint(client, name, f"{normalized}/health"))

    failed = [c for c in checks if not c.get("ok")]
    status = "ok" if not failed else "degraded"

    return {
        "status": status,
        "llm_model": settings.llm_model_name,
        "checks": checks,
        "failed_count": len(failed),
    }


@app.on_event("startup")
async def startup_event() -> None:
    if settings.db_init_on_startup:
        await init_db()
    else:
        logger.info("Skipping database initialization on startup (DB_INIT_ON_STARTUP=false)")
    _background_tasks.append(asyncio.create_task(numbeo_refresh_loop()))


@app.on_event("shutdown")
async def shutdown_event() -> None:
    for task in _background_tasks:
        task.cancel()
