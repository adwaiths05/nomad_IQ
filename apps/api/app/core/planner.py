from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agent import summarize_plan_with_trace


async def build_plan_outline(db: AsyncSession, city: str, start_date: str, end_date: str) -> dict:
    prompt = f"Create a concise trip outline for {city} from {start_date} to {end_date}."
    orchestrated = await summarize_plan_with_trace(prompt, db=db)
    summary = orchestrated.get("summary") or "Draft plan generated"
    return {
        "summary": summary,
        "city": city,
        "agentic_rag": {
            "component": "Agentic RAG Orchestrator",
            "tool_trace": orchestrated.get("tool_trace") or [],
            "retrieved_context_count": orchestrated.get("retrieved_context_count") or 0,
            "compressed_context": orchestrated.get("compressed_context") or "",
        },
    }
