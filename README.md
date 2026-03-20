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
