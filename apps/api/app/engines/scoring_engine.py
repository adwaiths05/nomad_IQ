def weighted_score(visual: float, crowd: float, lighting: float, uniqueness: float) -> float:
    return round((0.3 * visual) + (0.2 * crowd) + (0.2 * lighting) + (0.3 * uniqueness), 2)


def apply_trend_boost(score: float, is_trending: bool) -> float:
    if is_trending:
        return round(score + 20.0, 2)
    return round(score, 2)
