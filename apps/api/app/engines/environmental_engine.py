def aggregate_environment_score(transport: float, distance: float, crowd: float) -> float:
    return round((transport + distance + crowd) / 3, 2)
