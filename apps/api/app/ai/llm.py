from typing import Any

import httpx

from app.config.settings import get_settings

settings = get_settings()


async def chat_completion(messages: list[dict[str, str]], temperature: float = 0.2) -> dict[str, Any]:
    payload = {
        "model": settings.llm_model_name,
        "messages": messages,
        "temperature": temperature,
    }
    headers = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{settings.llm_base_url}/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
