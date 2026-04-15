def score_from_source(source_type: str) -> str:
    source = source_type.lower()
    if source in {
        "mcp_maps",
        "ticketmaster",
        "openweather",
        "openweather_plus_context",
        "apify_numbeo",
        "mcp_transport",
        "transport",
    }:
        return "high"
    if source in {"rag", "vector_db", "cached_api"}:
        return "medium"
    return "low"
