from app.ai.agent import summarize_plan


async def build_plan_outline(city: str, start_date: str, end_date: str) -> dict:
    prompt = f"Create a concise trip outline for {city} from {start_date} to {end_date}."
    summary = await summarize_plan(prompt)
    return {"summary": summary or "Draft plan generated", "city": city}
