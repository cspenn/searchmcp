"""DDGS engine registry and backend validation."""

ENGINE_REGISTRY: dict[str, frozenset[str]] = {
    "text": frozenset(
        {
            "brave",
            "duckduckgo",
            "google",
            "mojeek",
            "wikipedia",
            "grokipedia",
            "yahoo",
            "yandex",
        }
    ),
    "news": frozenset({"bing", "duckduckgo", "yahoo"}),
    "images": frozenset({"duckduckgo"}),
    "videos": frozenset({"duckduckgo"}),
    "books": frozenset({"annasarchive"}),
}

SPECIAL: frozenset[str] = frozenset({"auto", "all"})


def validate_backend(category: str, backend: str) -> str:
    """Validate comma-separated backend string against the category engine registry.

    Args:
        category: Search category (text/news/images/videos/books).
        backend: Single backend name, comma-separated names, or "auto"/"all".

    Returns:
        The validated backend string unchanged.

    Raises:
        ValueError: If any backend name is unsupported for the given category.
        ValueError: If category is not in ENGINE_REGISTRY.
    """
    if category not in ENGINE_REGISTRY:
        raise ValueError(
            f"Unknown search category: {category!r}. Valid: {sorted(ENGINE_REGISTRY)}"
        )
    valid = ENGINE_REGISTRY[category] | SPECIAL
    parts = [p.strip() for p in backend.split(",")]
    bad = [p for p in parts if p not in valid]
    if bad:
        raise ValueError(
            f"Unsupported backend(s) for {category!r}: {bad}. Valid: {sorted(valid)}"
        )
    return backend
