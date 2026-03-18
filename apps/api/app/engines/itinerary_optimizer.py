def optimize_itinerary(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda item: (item.get("day", 1), item.get("start_time", "09:00")))
