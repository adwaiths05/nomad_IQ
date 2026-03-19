from datetime import time


def _format_time(t: time | str | None) -> str:
    if t is None:
        return ""
    if isinstance(t, str):
        return t
    return t.strftime("%H:%M")


def _to_lightweight_block(start: time | str | None, end: time | str | None) -> str:
    start_hhmm = _format_time(start)
    end_hhmm = _format_time(end)
    hhmm = start_hhmm or end_hhmm
    if not hhmm:
        return "Flexible"

    hour = int(hhmm.split(":")[0])
    if 5 <= hour < 12:
        return "Morning"
    if 12 <= hour < 17:
        return "Afternoon"
    if 17 <= hour < 22:
        return "Evening"
    return "Night"


def _to_moderate_block(start: time | str | None, end: time | str | None) -> str:
    hhmm = _format_time(start) or _format_time(end)
    if not hhmm:
        return "12:00-15:00"
    hour = int(hhmm.split(":")[0])
    start_hour = max(0, min(hour, 21))
    end_hour = min(start_hour + 3, 24)
    return f"{start_hour:02d}:00-{end_hour:02d}:00"


def optimize_itinerary(items: list[dict], flexibility_level: str = "moderate") -> list[dict]:
    optimized = sorted(items, key=lambda item: (item.get("day", 1), item.get("start_time") or "09:00"))

    mode = flexibility_level.lower()
    if mode == "strict":
        return optimized

    if mode == "moderate":
        for item in optimized:
            item["time_block"] = _to_moderate_block(item.get("start_time"), item.get("end_time"))
            item["start_time"] = None
            item["end_time"] = None
        return optimized

    for item in optimized:
        item["time_block"] = _to_lightweight_block(item.get("start_time"), item.get("end_time"))
        item["start_time"] = None
        item["end_time"] = None

    return optimized
