from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_text
from app.models.memory import MemoryEmbedding
from app.schemas.memory import MemoryCreate, MemorySearchResult

ALLOWED_MEMORY_TYPES = {"short_term", "long_term", "external"}


def _keyword_set(text: str) -> set[str]:
    tokens = [token.strip(".,!?()[]{}\"'\n\t").lower() for token in text.split()]
    return {token for token in tokens if len(token) > 2}


def _keyword_match_ratio(query: str, content: str) -> float:
    query_tokens = _keyword_set(query)
    if not query_tokens:
        return 0.0
    content_tokens = _keyword_set(content)
    overlap = len(query_tokens.intersection(content_tokens))
    return overlap / max(len(query_tokens), 1)


def _semantic_similarity(distance: float) -> float:
    # Distance is 0 for identical vectors. Convert to a bounded similarity score.
    return max(0.0, min(1.0, 1.0 - float(distance)))


def _extract_memory_type(metadata: dict[str, Any] | None) -> str:
    if isinstance(metadata, dict):
        candidate = str(metadata.get("memory_type") or "").strip().lower()
        if candidate in ALLOWED_MEMORY_TYPES:
            return candidate
    return "long_term"


async def add_memory(db: AsyncSession, payload: MemoryCreate) -> MemoryEmbedding:
    vector = await embed_text(payload.content)
    memory_type = payload.memory_type.strip().lower() if payload.memory_type else "long_term"
    if memory_type not in ALLOWED_MEMORY_TYPES:
        memory_type = "long_term"
    metadata = dict(payload.metadata)
    metadata.setdefault("memory_type", memory_type)

    memory = MemoryEmbedding(
        user_id=payload.user_id,
        group_id=payload.group_id,
        content=payload.content,
        embedding=vector,
        model_metadata=metadata,
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory


async def search_memories(db: AsyncSession, query: str, user_id=None, group_id=None, limit: int = 5) -> list[MemoryEmbedding]:
    hybrid = await search_memories_hybrid(db, query, user_id=user_id, group_id=group_id, limit=limit)
    if not hybrid:
        return []

    ids = [item.id for item in hybrid]
    rows = await db.scalars(select(MemoryEmbedding).where(MemoryEmbedding.id.in_(ids)))
    by_id = {row.id: row for row in rows}
    ordered = [by_id[item_id] for item_id in ids if item_id in by_id]
    return ordered


async def search_memories_hybrid(
    db: AsyncSession,
    query: str,
    user_id=None,
    group_id=None,
    limit: int = 5,
    semantic_limit: int = 10,
    memory_type: str | None = None,
) -> list[MemorySearchResult]:
    requested_memory_type = memory_type.strip().lower() if isinstance(memory_type, str) else None
    if requested_memory_type and requested_memory_type not in ALLOWED_MEMORY_TYPES:
        requested_memory_type = None

    query_embedding = await embed_text(query)

    distance_expr = MemoryEmbedding.embedding.l2_distance(query_embedding)
    stmt = select(MemoryEmbedding, distance_expr.label("distance")).order_by(distance_expr).limit(max(semantic_limit, limit))
    if user_id is not None:
        stmt = stmt.where(MemoryEmbedding.user_id == user_id)
    if group_id is not None:
        stmt = stmt.where(MemoryEmbedding.group_id == group_id)

    rows = (await db.execute(stmt)).all()
    if not rows:
        return []

    scored: list[MemorySearchResult] = []
    total_rows = len(rows)
    for rank, (memory, distance) in enumerate(rows):
        current_memory_type = _extract_memory_type(memory.model_metadata)
        if requested_memory_type and current_memory_type != requested_memory_type:
            continue

        semantic = _semantic_similarity(float(distance))
        keyword = _keyword_match_ratio(query, memory.content)
        # Recency proxy: prefer newer rows among semantic matches when timestamps are unavailable.
        recency = 1.0 - (rank / max(total_rows - 1, 1))
        score = (0.6 * semantic) + (0.25 * keyword) + (0.15 * recency)

        scored.append(
            MemorySearchResult(
                id=memory.id,
                user_id=memory.user_id,
                group_id=memory.group_id,
                content=memory.content,
                metadata=memory.model_metadata,
                semantic_similarity=round(semantic, 4),
                keyword_match=round(keyword, 4),
                recency=round(recency, 4),
                score=round(score, 4),
                matched_queries=[query],
                memory_type=current_memory_type,
            )
        )

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]


async def search_memories_multi_query(
    db: AsyncSession,
    queries: list[str],
    user_id=None,
    group_id=None,
    limit: int = 5,
    semantic_limit: int = 10,
    memory_type: str | None = None,
) -> list[MemorySearchResult]:
    valid_queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
    if not valid_queries:
        return []

    merged: dict[Any, MemorySearchResult] = {}
    for query in valid_queries[:3]:
        items = await search_memories_hybrid(
            db,
            query=query,
            user_id=user_id,
            group_id=group_id,
            limit=max(limit, 5),
            semantic_limit=semantic_limit,
            memory_type=memory_type,
        )
        for item in items:
            existing = merged.get(item.id)
            if existing is None:
                merged[item.id] = item
                continue
            if item.score > existing.score:
                existing.semantic_similarity = item.semantic_similarity
                existing.keyword_match = item.keyword_match
                existing.recency = item.recency
                existing.score = item.score
            for q in item.matched_queries:
                if q not in existing.matched_queries:
                    existing.matched_queries.append(q)

    ranked = sorted(merged.values(), key=lambda item: item.score, reverse=True)
    return ranked[:limit]


def compute_memory_confidence(items: list[MemorySearchResult], query: str) -> float:
    if not items:
        return 0.0

    top = items[0]
    keyword_coverage = top.keyword_match
    confidence = (0.7 * top.semantic_similarity) + (0.3 * keyword_coverage)
    return round(max(0.0, min(1.0, confidence)), 4)
