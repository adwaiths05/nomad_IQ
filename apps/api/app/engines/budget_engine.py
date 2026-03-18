def estimate_daily_budget(total: int, days: int) -> int:
    safe_days = max(days, 1)
    return max(total // safe_days, 1)
