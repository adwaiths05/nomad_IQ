def score_from_source(source_type: str) -> str:
    source = source_type.lower()
    if source in {"google_places", "ticketmaster", "openweather", "amadeus", "numbeo_apify", "kiwi_mcp", "tequila_api"}:
        return "high"
    if source in {"rag", "vector_db", "cached_api"}:
        return "medium"
    return "low"
