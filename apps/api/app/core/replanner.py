def replan(existing_plan: dict, reason: str) -> dict:
    return {
        **existing_plan,
        "replanned": True,
        "replan_reason": reason,
        "changes": ["Adjusted ordering for weather and crowd conditions."],
    }
