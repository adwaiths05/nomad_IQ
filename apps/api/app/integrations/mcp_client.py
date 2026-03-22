from typing import Any

import httpx

from app.config.settings import get_settings


class FastMCPClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def call_tool(
        self,
        server_url: str | None,
        tool_name: str,
        arguments: dict[str, Any],
        tool_aliases: list[str] | None = None,
        timeout_seconds: int = 30,
    ) -> Any | None:
        if not self.settings.mcp_enabled:
            return None
        if not server_url or not tool_name:
            return None

        base_url = server_url.rstrip("/")
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.settings.mcp_auth_token:
            headers["Authorization"] = f"Bearer {self.settings.mcp_auth_token}"

        candidate_tool_names = self._dedupe_names([tool_name, *(tool_aliases or [])])

        # FastMCP deployments vary slightly in route naming; probe common paths.
        candidate_paths = ["/invoke", "/tools/call", "/tool/invoke"]

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            for current_tool_name in candidate_tool_names:
                payload = {
                    "tool": current_tool_name,
                    "arguments": arguments,
                }
                for path in candidate_paths:
                    try:
                        response = await client.post(f"{base_url}{path}", headers=headers, json=payload)
                    except httpx.HTTPError:
                        continue

                    if response.status_code == 404:
                        continue
                    if response.status_code in {400, 422}:
                        # Bad request often means wrong tool name/shape for this endpoint.
                        continue
                    if response.status_code >= 400:
                        return None

                    body = response.json()
                    return self._extract_result(body)

        return None

    def _dedupe_names(self, names: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for name in names:
            normalized = str(name or "").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
        return ordered

    def _extract_result(self, body: Any) -> Any | None:
        if body is None:
            return None

        if isinstance(body, (list, str, int, float, bool)):
            return body

        if not isinstance(body, dict):
            return None

        for key in ["result", "data", "output", "value"]:
            value = body.get(key)
            if value is not None:
                return value

        content = body.get("content")
        if isinstance(content, list):
            text_blocks = []
            for block in content:
                if isinstance(block, dict):
                    if isinstance(block.get("json"), dict):
                        return block["json"]
                    if isinstance(block.get("text"), str):
                        text_blocks.append(block["text"])
            if text_blocks:
                return "\n".join(text_blocks)

        return body
