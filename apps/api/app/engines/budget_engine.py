def estimate_daily_budget(total: int, days: int) -> int:
    safe_days = max(days, 1)
    return max(total // safe_days, 1)


def budget_pressure(actual_spent: int, estimated_total: int) -> float:
    if estimated_total <= 0:
        return 1.0
    return round(actual_spent / estimated_total, 4)


def suggest_cheaper_alternatives(
    pressure: float,
    city: str,
    baseline_daily: dict[str, float] | None = None,
) -> list[str]:
    if pressure < 0.8:
        return []

    category_suggestions = {
        "lodging": f"In {city}, move one tier down on lodging and prioritize stays near transit hubs.",
        "food": f"In {city}, switch to local cafes and set-menu lunches for most meals.",
        "activities": f"In {city}, replace one paid attraction daily with free public viewpoints or walking tours.",
        "transport": f"In {city}, use day-passes and metro-heavy routes instead of taxis.",
    }

    suggestions: list[str] = []
    if baseline_daily:
        ranked = sorted(
            ((k, v) for k, v in baseline_daily.items() if k in category_suggestions),
            key=lambda kv: kv[1],
            reverse=True,
        )
        for category, _ in ranked[:2]:
            suggestions.append(category_suggestions[category])

    if not suggestions:
        suggestions = [
            f"Use city transit day-passes in {city} instead of ride-hailing for non-essential trips.",
            "Prioritize lunch specials and local markets over high-demand dinner venues.",
        ]

    suggestions.append("Set a daily spend cap and review each evening to rebalance the next day.")
    if pressure >= 0.95:
        suggestions.append("Consolidate destinations by neighborhood to reduce same-day transit costs.")

    return suggestions
