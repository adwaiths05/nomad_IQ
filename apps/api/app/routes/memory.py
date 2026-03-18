from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.memory import MemoryCreate, MemoryRead, MemorySearchRequest
from app.services.memory_service import add_memory, search_memories

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("", response_model=MemoryRead)
async def create_memory(payload: MemoryCreate, db: AsyncSession = Depends(get_db)) -> MemoryRead:
    row = await add_memory(db, payload)
    return MemoryRead.model_validate(row)


@router.post("/search", response_model=list[MemoryRead])
async def search_memory(payload: MemorySearchRequest, db: AsyncSession = Depends(get_db)) -> list[MemoryRead]:
    rows = await search_memories(db, payload.query, payload.user_id, payload.group_id, payload.limit)
    return [MemoryRead.model_validate(row) for row in rows]
