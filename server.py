# start server.py
"""Web Search MCP Server using FastMCP and DuckDuckGo."""

import logging
import os
from dataclasses import dataclass
from typing import Any

from ddgs import DDGS  # type: ignore[import-not-found]
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Raised when a search operation fails."""

    pass


@dataclass
class TorConfig:
    """Tor proxy configuration for privacy-enhanced searches."""

    enabled: bool
    proxy: str
    timeout: int

    @classmethod
    def from_environment(cls) -> "TorConfig":
        """Load Tor configuration from environment variables.

        Environment Variables:
            SEARCHMCP_USE_TOR: Enable Tor routing (true/false/1/0/yes/no)
            SEARCHMCP_TOR_PROXY: Tor SOCKS proxy URL (default: socks5h://127.0.0.1:9050)
            SEARCHMCP_TOR_TIMEOUT: Request timeout in seconds (default: 30)

        Returns:
            TorConfig instance with settings from environment.
        """
        enabled = os.getenv("SEARCHMCP_USE_TOR", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        proxy = os.getenv("SEARCHMCP_TOR_PROXY", "socks5h://127.0.0.1:9050")
        timeout = int(os.getenv("SEARCHMCP_TOR_TIMEOUT", "30"))
        return cls(enabled=enabled, proxy=proxy, timeout=timeout)


# Module-level configuration (loaded once at startup)
_tor_config = TorConfig.from_environment()

# Log Tor status at module load
if _tor_config.enabled:
    logger.info(
        "Tor privacy mode ENABLED - all searches will route through %s",
        _tor_config.proxy,
    )
else:
    logger.info("Tor privacy mode disabled - searches will use direct connection")


mcp = FastMCP("Web Search")


def _get_ddgs_client() -> DDGS:
    """Create a DDGS client with optional Tor proxy.

    Returns:
        DDGS client configured based on Tor settings.
    """
    if _tor_config.enabled:
        return DDGS(proxy=_tor_config.proxy, timeout=_tor_config.timeout)
    return DDGS()


def _validate_search_params(
    query: str,
    max_results: int,
    safe_search: str | None = None,
) -> None:
    """Validate common search parameters.

    Args:
        query: The search query string.
        max_results: Maximum number of results.
        safe_search: Safety filter value (optional).

    Raises:
        ValueError: If any parameter is invalid.
    """
    if not query.strip():
        raise ValueError("Query cannot be empty")
    if not 1 <= max_results <= 100:
        raise ValueError("max_results must be between 1 and 100")
    if safe_search is not None and safe_search not in ("off", "moderate", "strict"):
        raise ValueError("safe_search must be 'off', 'moderate', or 'strict'")


def do_web_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: str = "moderate",
) -> list[dict[str, Any]]:
    """Execute web search using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-100).
        region: Region code (wt-wt = worldwide).
        safe_search: Safety filter (off/moderate/strict).

    Returns:
        List of results with title, href, and body fields.

    Raises:
        ValueError: If parameters are invalid.
        SearchError: If the search operation fails.
    """
    _validate_search_params(query, max_results, safe_search)
    try:
        logger.info("Web search: %s", query)
        client = _get_ddgs_client()
        results = client.text(
            query, max_results=max_results, region=region, safesearch=safe_search
        )
        logger.info("Web search returned %d results", len(results))
        return results
    except ValueError:
        raise
    except Exception as e:
        logger.error("Web search failed: %s", e)
        raise SearchError(f"Web search failed: {e}") from e


def do_image_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: str = "moderate",
) -> list[dict[str, Any]]:
    """Execute image search using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-100).
        region: Region code (wt-wt = worldwide).
        safe_search: Safety filter (off/moderate/strict).

    Returns:
        List of results with title, image, thumbnail, url, and source fields.

    Raises:
        ValueError: If parameters are invalid.
        SearchError: If the search operation fails.
    """
    _validate_search_params(query, max_results, safe_search)
    try:
        logger.info("Image search: %s", query)
        client = _get_ddgs_client()
        results = client.images(
            query, max_results=max_results, region=region, safesearch=safe_search
        )
        logger.info("Image search returned %d results", len(results))
        return results
    except ValueError:
        raise
    except Exception as e:
        logger.error("Image search failed: %s", e)
        raise SearchError(f"Image search failed: {e}") from e


def do_news_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
) -> list[dict[str, Any]]:
    """Execute news search using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-100).
        region: Region code (wt-wt = worldwide).

    Returns:
        List of results with title, url, body, date, and source fields.

    Raises:
        ValueError: If parameters are invalid.
        SearchError: If the search operation fails.
    """
    _validate_search_params(query, max_results)
    try:
        logger.info("News search: %s", query)
        client = _get_ddgs_client()
        results = client.news(query, max_results=max_results, region=region)
        logger.info("News search returned %d results", len(results))
        return results
    except ValueError:
        raise
    except Exception as e:
        logger.error("News search failed: %s", e)
        raise SearchError(f"News search failed: {e}") from e


@mcp.tool
def web_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: str = "moderate",
) -> list[dict[str, Any]]:
    """Search the web using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-100).
        region: Region code (wt-wt = worldwide).
        safe_search: Safety filter (off/moderate/strict).

    Returns:
        List of results with title, href, and body fields.
    """
    return do_web_search(query, max_results, region, safe_search)


@mcp.tool
def image_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: str = "moderate",
) -> list[dict[str, Any]]:
    """Search for images using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-100).
        region: Region code (wt-wt = worldwide).
        safe_search: Safety filter (off/moderate/strict).

    Returns:
        List of results with title, image, thumbnail, url, and source fields.
    """
    return do_image_search(query, max_results, region, safe_search)


@mcp.tool
def news_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
) -> list[dict[str, Any]]:
    """Search for news articles using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-100).
        region: Region code (wt-wt = worldwide).

    Returns:
        List of results with title, url, body, date, and source fields.
    """
    return do_news_search(query, max_results, region)


if __name__ == "__main__":
    mcp.run()
# end server.py
