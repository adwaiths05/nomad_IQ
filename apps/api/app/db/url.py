from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def normalize_async_database_url(raw_url: str) -> str:
    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]

    parts = urlsplit(url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    normalized_query: list[tuple[str, str]] = []
    unsupported_asyncpg_params = {
        "channel_binding",
        "gssencmode",
        "target_session_attrs",
        "krbsrvname",
        "gsslib",
        "requiressl",
        "passfile",
        "service",
    }
    for key, value in query:
        lowered = key.lower()
        if lowered == "sslmode":
            normalized_query.append(("ssl", value or "require"))
        elif lowered in unsupported_asyncpg_params:
            continue
        else:
            normalized_query.append((key, value))

    if normalized_query != query:
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(normalized_query), parts.fragment))
    return url
