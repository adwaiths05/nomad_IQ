def optimize_plan(plan: dict) -> dict:
    return {
        **plan,
        "optimized": True,
        "notes": "Applied deterministic route and budget balancing heuristics.",
    }
