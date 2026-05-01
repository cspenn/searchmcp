"""Web Search MCP Server using FastMCP and DuckDuckGo."""

import os
import socket
import sys
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlparse

import httpx
import typer
from ddgs import DDGS  # type: ignore[import-not-found]
from ddgs.exceptions import DDGSException  # type: ignore[import-not-found]
from fastmcp import FastMCP

from searchmcp.backends import validate_backend
from searchmcp.logging_config import configure_logging, get_logger
from searchmcp.params import SearchParams

configure_logging()
log = get_logger(__name__)

_with_logging = False


def verify_tor_proxy(proxy: str) -> bool:
    """Test connection to Tor SOCKS5 proxy.

    Args:
        proxy: Tor proxy URL (e.g., socks5h://127.0.0.1:9050)

    Returns:
        True if proxy is accepting connections, False otherwise.
    """
    try:
        parsed = urlparse(proxy)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 9050

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except (OSError, ValueError) as e:
        log.debug("tor_proxy_check_failed", error=str(e))
        return False


def verify_tor_exit(proxy: str, timeout: int) -> str:
    """Verify traffic is routing through Tor and return exit IP.

    Args:
        proxy: Tor proxy URL
        timeout: Request timeout in seconds

    Returns:
        Exit node IP address if verification succeeds.

    Raises:
        SystemExit: If Tor verification fails.
    """
    try:
        with httpx.Client(proxy=proxy, timeout=timeout) as client:
            response = client.get("https://check.torproject.org/api/ip")
        data = response.json()

        if not data.get("IsTor", False):
            log.error("tor_not_detected")
            sys.exit("ERROR: Tor verification failed - traffic not going through Tor")

        return data.get("IP", "unknown")
    except httpx.HTTPError as e:
        log.error("tor_connection_failed", error=str(e))
        sys.exit(f"ERROR: Could not verify Tor connection: {e}")


def check_privileges() -> None:
    """Warn if running with elevated privileges."""
    if os.name != "nt":
        if os.getuid() == 0:
            log.warning("running_as_root")
    else:  # pyright: ignore[reportUnreachable]  # pragma: no cover
        with suppress(AttributeError, OSError):
            import ctypes

            if ctypes.windll.shell32.IsUserAnAdmin():  # type: ignore[attr-defined]
                log.warning("running_as_admin")


def print_privacy_status(proxy: str, exit_ip: str) -> None:
    """Display privacy status and recommendations at startup.

    Args:
        proxy: Active Tor proxy URL
        exit_ip: Verified Tor exit node IP
    """
    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("  SEARCHMCP - Privacy Mode ENABLED")
    typer.echo("=" * 60)
    typer.echo("")
    typer.echo("  Privacy Checklist:")
    typer.echo(f"    [✓] Tor proxy: {proxy}")
    typer.echo(f"    [✓] Tor verified: exit IP {exit_ip}")
    typer.echo("    [✓] Query logging: DISABLED")
    typer.echo("")
    typer.echo("  For Maximum Privacy, Also Use:")
    typer.echo("    • VPN (layered with Tor for defense in depth)")
    typer.echo("    • Privacy browser (Tor Browser, Brave, Firefox with")
    typer.echo("      privacy extensions, or LibreWolf)")
    typer.echo("    • Encrypted email (ProtonMail, Tutanota, or self-hosted)")
    typer.echo("    • Encrypted messaging (Signal, Session, or Matrix)")
    typer.echo("    • Privacy-respecting DNS (Quad9, Mullvad DNS, NextDNS)")
    typer.echo("")
    typer.echo("  Threat Model Protection:")
    typer.echo("    • ISP surveillance: PROTECTED (Tor encryption)")
    typer.echo("    • Big Tech tracking: PROTECTED (no direct connection)")
    typer.echo("    • Network observers: PROTECTED (Tor routing)")
    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("")


class SearchError(Exception):
    """Raised when a search operation fails."""


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
            SEARCHMCP_USE_TOR: Enable Tor routing; Tor is enabled when the value (compared
                case-insensitively) is NOT in {'false', '0', 'no'}. Any other value,
                including an unset variable (default 'true'), enables Tor.
            SEARCHMCP_TOR_PROXY: Tor SOCKS proxy URL (default: socks5h://127.0.0.1:9050)
            SEARCHMCP_TOR_TIMEOUT: Request timeout in seconds (default: 30)

        Returns:
            TorConfig instance with settings from environment.
        """
        enabled = os.getenv("SEARCHMCP_USE_TOR", "true").lower() not in (
            "false",
            "0",
            "no",
        )
        proxy = os.getenv("SEARCHMCP_TOR_PROXY", "socks5h://127.0.0.1:9050")
        timeout = int(os.getenv("SEARCHMCP_TOR_TIMEOUT", "30"))
        return cls(enabled=enabled, proxy=proxy, timeout=timeout)


_tor_config = TorConfig.from_environment()

if _tor_config.enabled:
    log.info("tor_enabled", proxy=_tor_config.proxy)
else:  # pragma: no cover
    log.info("tor_disabled")


_ddgs_client: Any = None


def configure(*, with_logging: bool, tor_config: TorConfig | None = None) -> TorConfig:
    """Apply CLI/runtime configuration. Call once before mcp.run().

    Returns:
        The active TorConfig after applying changes.
    """
    global _with_logging, _tor_config, _ddgs_client
    _with_logging = with_logging
    if tor_config is not None:
        _tor_config = tor_config
    _ddgs_client = None
    return _tor_config


mcp = FastMCP("Web Search")


def _get_ddgs_client() -> Any:
    """Return the module-level DDGS singleton, creating it on first call."""
    global _ddgs_client
    if _ddgs_client is None:
        _ddgs_client = (
            DDGS(proxy=_tor_config.proxy, timeout=_tor_config.timeout)
            if _tor_config.enabled
            else DDGS()
        )
    return _ddgs_client


def _validate_query(query: str) -> None:
    """Raise ValueError if query is blank.

    Args:
        query: The search query to validate.

    Raises:
        ValueError: If query is empty or whitespace only.
    """
    if not query.strip():
        raise ValueError("Query cannot be empty")


def _do_search(
    category: Literal["text", "news", "images", "videos", "books"],
    query: str,
    params: SearchParams | None = None,
) -> list[dict[str, Any]]:
    """Execute a search against the given DDGS category.

    Args:
        category: DDGS method name (text/news/images/videos/books).
        query: The search query string.
        params: Search parameters; defaults to SearchParams() if None.

    Returns:
        List of result dicts.

    Raises:
        ValueError: If query is empty or backend is invalid for the category.
        SearchError: If the DDGS search operation fails.
    """
    if params is None:
        params = SearchParams()
    _validate_query(query)
    validate_backend(category, params.backend)
    try:
        if _with_logging:
            log.info(f"{category}_search_started", query=query)
        else:
            log.info(f"{category}_search_performed")
        client = _get_ddgs_client()
        results: list[dict[str, Any]] = getattr(client, category)(
            query,
            max_results=params.max_results,
            region=params.region,
            safesearch=params.safesearch,
            timelimit=params.timelimit,
            backend=params.backend,
            page=params.page,
        )
        log.info(f"{category}_search_completed", count=len(results))
        return results
    except ValueError:
        raise
    except DDGSException as e:
        log.error(f"{category}_search_failed", error=str(e))
        raise SearchError(f"{category} search failed: {e}") from e
    except Exception as e:
        log.error(f"{category}_search_failed", error=str(e))
        raise SearchError(f"{category} search failed: {e}") from e


def do_web_search(
    query: str, params: SearchParams | None = None
) -> list[dict[str, Any]]:
    """Execute web search using DuckDuckGo.

    Args:
        query: The search query string.
        params: Search parameters (max_results, region, safesearch, timelimit, backend, page).

    Returns:
        List of results with title, href, and body fields.

    Raises:
        ValueError: If parameters are invalid.
        SearchError: If the search operation fails.
    """
    return _do_search("text", query, params)


def do_image_search(
    query: str, params: SearchParams | None = None
) -> list[dict[str, Any]]:
    """Execute image search using DuckDuckGo.

    Args:
        query: The search query string.
        params: Search parameters (max_results, region, safesearch, timelimit, backend, page).

    Returns:
        List of results with title, image, thumbnail, url, height, width, and source fields.

    Raises:
        ValueError: If parameters are invalid.
        SearchError: If the search operation fails.
    """
    return _do_search("images", query, params)


def do_news_search(
    query: str, params: SearchParams | None = None
) -> list[dict[str, Any]]:
    """Execute news search using DuckDuckGo.

    Args:
        query: The search query string.
        params: Search parameters (max_results, region, safesearch, timelimit, backend, page).

    Returns:
        List of results with title, url, body, date, image, and source fields.

    Raises:
        ValueError: If parameters are invalid.
        SearchError: If the search operation fails.
    """
    return _do_search("news", query, params)


def do_videos_search(
    query: str, params: SearchParams | None = None
) -> list[dict[str, Any]]:
    """Execute video search using DuckDuckGo.

    Args:
        query: The search query string.
        params: Search parameters (max_results, region, safesearch, timelimit, backend, page).

    Returns:
        List of results with title, content, description, duration, embed_html, embed_url,
        image_token, images, provider, published, publisher, statistics, and uploader fields.

    Raises:
        ValueError: If parameters are invalid.
        SearchError: If the search operation fails.
    """
    return _do_search("videos", query, params)


def do_books_search(
    query: str, params: SearchParams | None = None
) -> list[dict[str, Any]]:
    """Execute book search using DuckDuckGo.

    Args:
        query: The search query string.
        params: Search parameters (max_results, region, safesearch, timelimit, backend, page).

    Returns:
        List of results with title, author, publisher, info, url, and thumbnail fields.

    Raises:
        ValueError: If parameters are invalid.
        SearchError: If the search operation fails.
    """
    return _do_search("books", query, params)


@mcp.tool
def web_search(  # noqa: PLR0913
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
    timelimit: Literal["d", "w", "m", "y"] | None = None,
    backend: str = "auto",
    page: int = 1,
) -> list[dict[str, Any]]:
    """Search the web using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-100).
        region: Region code (wt-wt = worldwide).
        safe_search: Safety filter (off/moderate/strict).
        timelimit: Time limit (d=day, w=week, m=month, y=year).
        backend: Search engine backend(s); single name, comma-separated, or auto/all.
        page: Result page number (1-100).

    Returns:
        List of results with title, href, and body fields.
    """
    params = SearchParams(
        max_results=max_results,
        region=region,
        safesearch=safe_search,
        timelimit=timelimit,
        backend=backend,
        page=page,
    )
    return do_web_search(query, params)


@mcp.tool
def image_search(  # noqa: PLR0913
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
    timelimit: Literal["d", "w", "m", "y"] | None = None,
    backend: str = "auto",
    page: int = 1,
) -> list[dict[str, Any]]:
    """Search for images using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-100).
        region: Region code (wt-wt = worldwide).
        safe_search: Safety filter (off/moderate/strict).
        timelimit: Time limit (d=day, w=week, m=month, y=year).
        backend: Search engine backend(s); single name, comma-separated, or auto/all.
        page: Result page number (1-100).

    Returns:
        List of results with title, image, thumbnail, url, height, width, and source fields.
    """
    params = SearchParams(
        max_results=max_results,
        region=region,
        safesearch=safe_search,
        timelimit=timelimit,
        backend=backend,
        page=page,
    )
    return do_image_search(query, params)


@mcp.tool
def news_search(  # noqa: PLR0913
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
    timelimit: Literal["d", "w", "m", "y"] | None = None,
    backend: str = "auto",
    page: int = 1,
) -> list[dict[str, Any]]:
    """Search for news articles using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-100).
        region: Region code (wt-wt = worldwide).
        safe_search: Safety filter (off/moderate/strict).
        timelimit: Time limit (d=day, w=week, m=month, y=year).
        backend: Search engine backend(s); single name, comma-separated, or auto/all.
        page: Result page number (1-100).

    Returns:
        List of results with title, url, body, date, image, and source fields.
    """
    params = SearchParams(
        max_results=max_results,
        region=region,
        safesearch=safe_search,
        timelimit=timelimit,
        backend=backend,
        page=page,
    )
    return do_news_search(query, params)


@mcp.tool
def videos_search(  # noqa: PLR0913
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
    timelimit: Literal["d", "w", "m", "y"] | None = None,
    backend: str = "auto",
    page: int = 1,
) -> list[dict[str, Any]]:
    """Search for videos using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-100).
        region: Region code (wt-wt = worldwide).
        safe_search: Safety filter (off/moderate/strict).
        timelimit: Time limit (d=day, w=week, m=month, y=year).
        backend: Search engine backend(s); single name, comma-separated, or auto/all.
        page: Result page number (1-100).

    Returns:
        List of results with title, content, description, duration, embed_html, embed_url,
        image_token, images, provider, published, publisher, statistics, and uploader fields.
    """
    params = SearchParams(
        max_results=max_results,
        region=region,
        safesearch=safe_search,
        timelimit=timelimit,
        backend=backend,
        page=page,
    )
    return do_videos_search(query, params)


@mcp.tool
def books_search(  # noqa: PLR0913
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
    timelimit: Literal["d", "w", "m", "y"] | None = None,
    backend: str = "auto",
    page: int = 1,
) -> list[dict[str, Any]]:
    """Search for books using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results (1-100).
        region: Region code (wt-wt = worldwide).
        safe_search: Safety filter (off/moderate/strict).
        timelimit: Time limit (d=day, w=week, m=month, y=year).
        backend: Search engine backend(s); single name, comma-separated, or auto/all.
        page: Result page number (1-100).

    Returns:
        List of results with title, author, publisher, info, url, and thumbnail fields.
    """
    params = SearchParams(
        max_results=max_results,
        region=region,
        safesearch=safe_search,
        timelimit=timelimit,
        backend=backend,
        page=page,
    )
    return do_books_search(query, params)
