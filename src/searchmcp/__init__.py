"""searchmcp - Privacy-first web search MCP server and CLI."""

from searchmcp.params import SearchParams
from searchmcp.server import (
    SearchError,
    TorConfig,
    configure,
    mcp,
    web_search,
    image_search,
    news_search,
    videos_search,
    books_search,
    do_web_search,
    do_image_search,
    do_news_search,
    do_videos_search,
    do_books_search,
)

__all__ = [
    "SearchError",
    "SearchParams",
    "TorConfig",
    "configure",
    "mcp",
    "web_search",
    "image_search",
    "news_search",
    "videos_search",
    "books_search",
    "do_web_search",
    "do_image_search",
    "do_news_search",
    "do_videos_search",
    "do_books_search",
]
