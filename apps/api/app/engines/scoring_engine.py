def weighted_score(visual: float, crowd: float, lighting: float, uniqueness: float) -> float:
    return round((0.3 * visual) + (0.2 * crowd) + (0.2 * lighting) + (0.3 * uniqueness), 2)
