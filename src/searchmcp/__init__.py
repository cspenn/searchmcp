# start src/searchmcp/__init__.py
"""searchmcp - Privacy-first web search MCP server."""

from searchmcp.server import (
    SearchError,
    TorConfig,
    mcp,
    web_search,
    image_search,
    news_search,
    do_web_search,
    do_image_search,
    do_news_search,
)

__all__ = [
    "SearchError",
    "TorConfig",
    "mcp",
    "web_search",
    "image_search",
    "news_search",
    "do_web_search",
    "do_image_search",
    "do_news_search",
]
# end src/searchmcp/__init__.py
