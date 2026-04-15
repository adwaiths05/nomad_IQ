import asyncio
import json
import os
import shlex
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


@dataclass
class MCPResponse:
    id: int
    payload: dict[str, Any]


class MCPToolCallRequest(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class MCPStdioClient:
    def __init__(self, command: str) -> None:
        self.command = command
        self.framing = os.getenv("MCP_STDIO_FRAMING", "ndjson").strip().lower()
        self.process: asyncio.subprocess.Process | None = None
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.stderr_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._counter = 0

    async def start(self) -> None:
        async with self._lock:
            await self._start_unlocked()

    async def _start_unlocked(self) -> None:
        if self.process and self.process.returncode is None:
            return

        cmd_parts = shlex.split(self.command)
        if not cmd_parts:
            raise RuntimeError("MCP_COMMAND is empty")

        self.process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy(),
        )
        if self.process.stdout is None or self.process.stdin is None:
            raise RuntimeError("Failed to create stdio pipes for MCP process")

        self.reader = self.process.stdout
        self.writer = self.process.stdin

        if self.process.stderr is not None:
            self.stderr_task = asyncio.create_task(self._drain_stderr(self.process.stderr))

        init_payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "nomadiq-mcp-bridge",
                    "version": "1.0.0",
                },
            },
        }
        await self._send_json(init_payload)
        await self._wait_for_id(init_payload["id"], timeout=25)

        await self._send_json(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }
        )

    async def stop(self) -> None:
        async with self._lock:
            if self.process is None:
                return

            self.process.terminate()
            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self.process.wait(), timeout=5)

            if self.process.returncode is None:
                self.process.kill()
                with suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(self.process.wait(), timeout=5)

            self.process = None
            self.reader = None
            self.writer = None
            if self.stderr_task is not None:
                self.stderr_task.cancel()
                with suppress(asyncio.CancelledError):
                    await self.stderr_task
                self.stderr_task = None

    def _next_id(self) -> int:
        self._counter += 1
        return self._counter

    async def call_tool(self, tool: str, arguments: dict[str, Any]) -> Any:
        async with self._lock:
            await self._start_unlocked()

            req_id = self._next_id()
            payload = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "tools/call",
                "params": {
                    "name": tool,
                    "arguments": arguments,
                },
            }
            await self._send_json(payload)
            response = await self._wait_for_id(req_id, timeout=60)

            if "error" in response.payload:
                error = response.payload["error"]
                raise RuntimeError(f"MCP error: {error}")

            return response.payload.get("result")

    async def _send_json(self, payload: dict[str, Any]) -> None:
        if self.writer is None:
            raise RuntimeError("MCP writer is not initialized")

        body = json.dumps(payload).encode("utf-8")
        if self.framing == "content-length":
            header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
            self.writer.write(header + body)
        else:
            # FastMCP Python servers in this repo use NDJSON framing.
            self.writer.write(body + b"\n")
        await self.writer.drain()

    async def _wait_for_id(self, req_id: int, timeout: int) -> MCPResponse:
        async def _wait() -> MCPResponse:
            while True:
                payload = await self._read_json_message()
                if isinstance(payload, dict) and payload.get("id") == req_id:
                    return MCPResponse(id=req_id, payload=payload)

        return await asyncio.wait_for(_wait(), timeout=timeout)

    async def _read_json_message(self) -> dict[str, Any] | list[Any]:
        if self.reader is None:
            raise RuntimeError("MCP reader is not initialized")

        while True:
            first = await self.reader.readline()
            if not first:
                raise RuntimeError("MCP process closed stdout")

            first_decoded = first.decode("utf-8", errors="replace").strip()
            if not first_decoded:
                continue

            # Ignore accidental stdout logs and keep reading until JSON-RPC frame appears.
            if not (
                first_decoded.startswith("{")
                or first_decoded.startswith("[")
                or first_decoded.lower().startswith("content-length:")
            ):
                continue
            break

        # Fallback support for Content-Length framed servers.
        if first_decoded.lower().startswith("content-length:"):
            headers: dict[str, str] = {}
            header_line = first_decoded
            while True:
                if ":" in header_line:
                    key, value = header_line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()

                next_line = await self.reader.readline()
                if not next_line:
                    raise RuntimeError("MCP process closed stdout")
                header_line = next_line.decode("utf-8", errors="replace").strip()
                if header_line == "":
                    break

            if "content-length" not in headers:
                raise RuntimeError("Invalid MCP message: missing Content-Length")

            length = int(headers["content-length"])
            body = await self.reader.readexactly(length)
            return json.loads(body.decode("utf-8"))

        # NDJSON framing: one JSON message per line.
        return json.loads(first_decoded)

    async def _drain_stderr(self, stream: asyncio.StreamReader) -> None:
        while True:
            chunk = await stream.readline()
            if not chunk:
                break
            # Log stderr output so we can debug subprocess issues
            import sys
            sys.stderr.write(f"[MCP STDERR] {chunk.decode('utf-8', errors='replace')}")
            sys.stderr.flush()


command = os.getenv("MCP_COMMAND", "").strip()
if not command:
    raise RuntimeError("MCP_COMMAND environment variable is required")

client = MCPStdioClient(command=command)
app = FastAPI(title="MCP Stdio Bridge", version="1.0.0")


@app.on_event("startup")
async def on_startup() -> None:
    await client.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await client.stop()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/invoke")
@app.post("/tools/call")
@app.post("/tool/invoke")
async def invoke(request: MCPToolCallRequest) -> dict[str, Any]:
    try:
        result = await client.call_tool(tool=request.tool, arguments=request.arguments)
        return {"result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
