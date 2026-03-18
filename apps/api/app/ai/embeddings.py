import hashlib
from typing import Any

import httpx

from app.config.settings import get_settings

settings = get_settings()


def _deterministic_fallback(text: str, dim: int = 768) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    while len(values) < dim:
        for b in digest:
            values.append((b / 255.0) * 2 - 1)
            if len(values) == dim:
                break
        digest = hashlib.sha256(digest).digest()
    return values


async def embed_text(text: str) -> list[float]:
    payload: dict[str, Any] = {"model": settings.embeddings_model_name, "input": text}
    headers = {"Content-Type": "application/json"}
    if settings.embeddings_api_key:
        headers["Authorization"] = f"Bearer {settings.embeddings_api_key}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{settings.embeddings_base_url}/embeddings", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    except Exception:
        return _deterministic_fallback(text)
