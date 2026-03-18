from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_text
from app.models.memory import MemoryEmbedding
from app.schemas.memory import MemoryCreate


async def add_memory(db: AsyncSession, payload: MemoryCreate) -> MemoryEmbedding:
    vector = await embed_text(payload.content)
    memory = MemoryEmbedding(
        user_id=payload.user_id,
        group_id=payload.group_id,
        content=payload.content,
        embedding=vector,
        metadata=payload.metadata,
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory


async def search_memories(db: AsyncSession, query: str, user_id=None, group_id=None, limit: int = 5) -> list[MemoryEmbedding]:
    rows = await db.scalars(select(MemoryEmbedding).order_by(MemoryEmbedding.id.desc()).limit(limit))
    return list(rows)
