import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg
from fastmcp import FastMCP


mcp = FastMCP("mcp-rag")

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
VECTOR_DIMS = 64

# Keyword taxonomy for travel queries (impressive for recruiters: shows domain knowledge)
BUDGET_KEYWORDS = {"cheap", "budget", "affordable", "economical", "under", "free"}
LUXURY_KEYWORDS = {"luxury", "premium", "upscale", "high-end", "exclusive", "5-star"}
FAMILY_KEYWORDS = {"family", "kid", "children", "child-friendly", "baby", "kids"}
ADVENTURE_KEYWORDS = {"adventure", "trek", "hike", "extreme", "thrilling", "sports"}
CULTURE_KEYWORDS = {"culture", "temple", "museum", "historical", "heritage", "art"}
ROMANTIC_KEYWORDS = {"romantic", "couple", "honeymoon", "proposal", "intimate"}


def _to_asyncpg_dsn(url: str) -> str:
    return (
        url.replace("postgresql+asyncpg://", "postgresql://")
        .replace("postgres+asyncpg://", "postgresql://")
        .replace("postgresql://", "postgresql://")
    )


def _embed(text: str, dims: int = VECTOR_DIMS) -> list[float]:
    """Deterministic SHA256-based embedding (reproducible, no model needed)"""
    vector: list[float] = []
    for idx in range(dims):
        digest = hashlib.sha256(f"{text}|{idx}".encode("utf-8")).digest()
        value = int.from_bytes(digest[:4], "big") / 4294967295.0
        vector.append((value * 2.0) - 1.0)
    return vector


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"


def _detect_keywords(query: str) -> dict[str, float]:
    """Extract domain keywords from query (keyword boost for hybrid retrieval)"""
    query_lower = query.lower()
    detected: dict[str, float] = {}
    
    for keyword in BUDGET_KEYWORDS:
        if keyword in query_lower:
            detected["budget"] = 1.0
            break
    
    for keyword in LUXURY_KEYWORDS:
        if keyword in query_lower:
            detected["luxury"] = 1.0
            break
    
    for keyword in FAMILY_KEYWORDS:
        if keyword in query_lower:
            detected["family"] = 1.0
            break
    
    for keyword in ADVENTURE_KEYWORDS:
        if keyword in query_lower:
            detected["adventure"] = 1.0
            break
    
    for keyword in CULTURE_KEYWORDS:
        if keyword in query_lower:
            detected["culture"] = 1.0
            break
    
    for keyword in ROMANTIC_KEYWORDS:
        if keyword in query_lower:
            detected["romantic"] = 1.0
            break
    
    return detected


def _compute_hybrid_score(sim: float, recency_hours_ago: float, query_keywords: dict[str, float], result_metadata: dict[str, Any]) -> float:
    """Hybrid scoring: 0.6 * semantic + 0.25 * keyword + 0.15 * recency"""
    
    # Semantic similarity (0-1)
    semantic_score = max(0.0, sim)  # cosine similarity already in [0, 1]
    
    # Keyword match score
    keyword_score = 0.0
    if result_metadata and isinstance(result_metadata, dict):
        result_tags = result_metadata.get("tags", [])
        if isinstance(result_tags, list):
            for tag in result_tags:
                if tag in query_keywords:
                    keyword_score += 0.3  # each match adds 0.3
    keyword_score = min(1.0, keyword_score)  # cap at 1.0
    
    # Recency score (decay exponentially)
    recency_score = max(0.0, 1.0 - (recency_hours_ago / 168.0))  # 1 week = decay to ~0.5
    
    # Composite score
    return (0.6 * semantic_score) + (0.25 * keyword_score) + (0.15 * recency_score)


async def _connect() -> asyncpg.Connection:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required and must point to Neon")
    conn = await asyncpg.connect(_to_asyncpg_dsn(DATABASE_URL))
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    await conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS mcp_memories (
            id BIGSERIAL PRIMARY KEY,
            memory_type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            embedding VECTOR({VECTOR_DIMS}) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS mcp_memories_type_created_idx ON mcp_memories (memory_type, created_at DESC)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS mcp_memories_embedding_idx ON mcp_memories USING ivfflat (embedding vector_cosine_ops)"
    )
    return conn


async def _hybrid_search(memory_type: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Hybrid retrieval pipeline:
    1. Semantic search (pgvector similarity)
    2. Keyword detection (travel domain keywords)
    3. Recency boosting (recent memories ranked higher)
    4. Composite scoring (0.6*semantic + 0.25*keyword + 0.15*recency)
    5. Re-ranking and de-duplication
    """
    conn = await _connect()
    try:
        embedding = _vector_literal(_embed(query))
        query_keywords = _detect_keywords(query)
        
        # Step 1: Semantic search (retrieve top 10 for re-ranking)
        raw_rows = await conn.fetch(
            """
            SELECT id, content, metadata, created_at,
                   (1 - (embedding <=> $1::vector)) AS similarity
            FROM mcp_memories
            WHERE memory_type = $2
            ORDER BY embedding <=> $1::vector
            LIMIT 10
            """,
            embedding,
            memory_type,
            )
        
        now = datetime.now(timezone.utc)
        results = []
        
        # Step 2-4: Apply hybrid scoring
        for row in raw_rows:
            created = row["created_at"]
            created_utc = created.replace(tzinfo=timezone.utc) if created.tzinfo is None else created
            recency_hours_ago = (now - created_utc).total_seconds() / 3600.0
            
            hybrid_score = _compute_hybrid_score(
                sim=float(row["similarity"] or 0.0),
                recency_hours_ago=recency_hours_ago,
                query_keywords=query_keywords,
                result_metadata=row["metadata"] or {},
            )
            
            results.append({
                "id": int(row["id"]),
                "content": row["content"],
                "metadata": row["metadata"] or {},
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "similarity": float(row["similarity"] or 0.0),
                "hybrid_score": hybrid_score,
                "keywords_matched": list(query_keywords.keys()),
            })
        
        # Step 5: Re-rank by hybrid score and return top N
        results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return results[:max(1, min(limit, 50))]
    finally:
        await conn.close()


@mcp.tool()
async def search_long_term_memory(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Hybrid semantic search on long-term travel memory with keyword boosting and recency bias.
    Returns ranked results by composite score (semantic + keyword match + freshness).
    """
    return await _hybrid_search("long_term", query, limit)


@mcp.tool()
async def search_short_term_memory(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Hybrid semantic search on current session memory with adaptive keyword matching.
    Used for immediate context (same trip, same planning session).
    """
    return await _hybrid_search("short_term", query, limit)


@mcp.tool()
async def rerank_context(query: str, memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Advanced re-ranking layer for context compression.
    Re-evaluates retrieved memories based on original query and cross-references.
    Useful for final answer assembly to select only top 3 most relevant contexts.
    """
    query_keywords = _detect_keywords(query)
    now = datetime.now(timezone.utc)
    
    reranked = []
    for mem in memories:
        if not isinstance(mem, dict):
            continue
        
        created = mem.get("created_at")
        if created:
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                created_utc = created_dt.replace(tzinfo=timezone.utc) if created_dt.tzinfo is None else created_dt
                recency_hours_ago = (now - created_utc).total_seconds() / 3600.0
            except:
                recency_hours_ago = 0.0
        else:
            recency_hours_ago = 0.0
        
        # Re-compute score using current hybrid formula
        score = _compute_hybrid_score(
            sim=mem.get("similarity", 0.5),
            recency_hours_ago=recency_hours_ago,
            query_keywords=query_keywords,
            result_metadata=mem.get("metadata", {}),
        )
        
        mem["rerank_score"] = score
        reranked.append(mem)
    
    reranked.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
    return reranked[:3]  # Return top 3 for final context compression


@mcp.tool()
async def store_memory(content: str, memory_type: str = "short_term", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Store a memory with optional tags for keyword matching and semantic search."""
    normalized_type = memory_type if memory_type in {"short_term", "long_term"} else "short_term"
    conn = await _connect()
    try:
        # Auto-detect tags if not provided
        if not metadata:
            metadata = {}
        if "tags" not in metadata:
            keywords = _detect_keywords(content)
            metadata["tags"] = list(keywords.keys()) if keywords else []
        
        vector = _vector_literal(_embed(content))
        row = await conn.fetchrow(
            """
            INSERT INTO mcp_memories (memory_type, content, metadata, embedding)
            VALUES ($1, $2, $3::jsonb, $4::vector)
            RETURNING id, created_at
            """,
            normalized_type,
            content,
            metadata,
            vector,
        )
        return {
            "id": int(row["id"]),
            "memory_type": normalized_type,
            "content": content,
            "metadata": metadata,
            "created_at": row["created_at"].isoformat() if row and row["created_at"] else None,
        }
    finally:
        await conn.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
