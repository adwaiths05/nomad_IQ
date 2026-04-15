from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.memory import MemoryCreate, MemoryRead, MemorySearchRequest, MemoryToolSearchResponse
from app.services.memory_service import (
    add_memory,
    compute_memory_confidence,
    search_memories,
    search_memories_hybrid,
    search_memories_multi_query,
)

router = APIRouter(prefix="/memory", tags=["memory"])


def _to_memory_read(row) -> MemoryRead:
    return MemoryRead(
        id=row.id,
        user_id=row.user_id,
        group_id=row.group_id,
        content=row.content,
        metadata=row.model_metadata,
    )


@router.post("", response_model=MemoryRead)
async def create_memory(payload: MemoryCreate, db: AsyncSession = Depends(get_db)) -> MemoryRead:
    row = await add_memory(db, payload)
    return _to_memory_read(row)


@router.post("/search", response_model=list[MemoryRead])
async def search_memory(payload: MemorySearchRequest, db: AsyncSession = Depends(get_db)) -> list[MemoryRead]:
    rows = await search_memories(db, payload.query, payload.user_id, payload.group_id, payload.limit)
    return [_to_memory_read(row) for row in rows]


@router.post("/search-tool", response_model=MemoryToolSearchResponse)
async def search_memory_tool(payload: MemorySearchRequest, db: AsyncSession = Depends(get_db)) -> MemoryToolSearchResponse:
    queries = [payload.query]
    items = await search_memories_multi_query(
        db,
        queries=queries,
        user_id=payload.user_id,
        group_id=payload.group_id,
        limit=payload.limit,
        memory_type=payload.memory_type,
    )
    confidence = compute_memory_confidence(items, payload.query)
    return MemoryToolSearchResponse(query=payload.query, confidence=confidence, count=len(items), items=items)
