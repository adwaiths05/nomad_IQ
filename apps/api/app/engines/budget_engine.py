def estimate_daily_budget(total: int, days: int) -> int:
    safe_days = max(days, 1)
    return max(total // safe_days, 1)


def budget_pressure(actual_spent: int, estimated_total: int) -> float:
    if estimated_total <= 0:
        return 1.0
    return round(actual_spent / estimated_total, 4)


def suggest_cheaper_alternatives(pressure: float, city: str) -> list[str]:
    if pressure < 0.8:
        return []

    suggestions = [
        f"Use city transit day-passes in {city} instead of ride-hailing for non-essential trips.",
        "Prioritize lunch specials and local markets over high-demand dinner venues.",
        "Swap one paid attraction for a free walking route or public viewpoint each day.",
    ]
    if pressure >= 0.95:
        suggestions.append("Reallocate budget from activities to lodging by choosing a lower nightly tier.")
        suggestions.append("Consolidate destinations by neighborhood to reduce same-day transit costs.")

    return suggestions
