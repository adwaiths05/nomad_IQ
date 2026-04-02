# Nomadiq

AI-powered trip planning monorepo.

## Stack

- Frontend: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Vercel AI SDK
- Backend: FastAPI, Pydantic v2, SQLAlchemy 2.0 async, httpx
- AI: PydanticAI + custom orchestration
- Model serving: vLLM (OpenAI-compatible), text-embeddings-inference
- Database: Neon PostgreSQL + pgvector
- Auth: JWT + bcrypt + refresh tokens

## Monorepo Structure

- `apps/api` FastAPI backend
- `apps/web` Next.js frontend (to be added)
- `docker/llm` vLLM compose
- `docker/embeddings` embedding service compose
- `docker/api` backend compose

## Backend Setup

1. Copy `.env.example` values into your runtime environment.
2. Install dependencies:

```bash
cd apps/api
pip install -r requirements.txt
```

3. Run API:

```bash
cd apps/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Services

## One Command Docker Setup

Run the full stack (Postgres, Redis, API, Frontend, MCP bridges, vLLM, embeddings) from the repository root:

```bash
docker compose up --build
```

Core service URLs after startup:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- MCP Google Maps bridge: `http://localhost:9101`
- MCP Ticketmaster bridge: `http://localhost:9102`
- MCP OpenWeather bridge: `http://localhost:9103`
- MCP Apify bridge: `http://localhost:9104`
- Startup readiness endpoint: `http://localhost:8000/health/startup`

The MCP bridges convert stdio MCP servers to HTTP invoke endpoints (`/invoke`, `/tools/call`, `/tool/invoke`) so the backend can call MCP tools reliably in Docker.

Required environment variables for external MCP providers:

- `GOOGLE_MAPS_API_KEY`
- `TICKETMASTER_API_KEY`
- `OPENWEATHER_API_KEY`
- `APIFY_API_TOKEN`

Optional Apify actor IDs:

- `MCP_APIFY_NUMBEO_ACTOR_ID`
- `MCP_APIFY_NEWS_ACTOR_ID` (defaults to `GetLatestNewsOnTopic`)

vLLM model default in Docker is set to:

- `Qwen/Qwen2.5-7B-Instruct-AWQ`

The vLLM command is configured for AWQ quantization (`--quantization awq`) and automatic dtype selection.

### vLLM

```bash
cd docker/llm
docker compose up -d
```

### Embeddings

```bash
cd docker/embeddings
docker compose up -d
```

### API

```bash
cd docker/api
docker compose up -d --build
```

## Notes

- The backend now enforces env-only behavior for key runtime values:
  - `DATABASE_URL`
  - `JWT_SECRET_KEY`
  - `LLM_BASE_URL`
  - `LLM_MODEL_NAME`
  - `EMBEDDINGS_BASE_URL`
  - `EMBEDDINGS_MODEL_NAME`
- API keys are not generated in code.
- External providers are consumed via MCP servers (Google Maps, Composio-based providers, and custom FastMCP wrappers).
