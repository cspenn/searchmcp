"""Web Search MCP Server using FastMCP and DuckDuckGo."""

import logging
import os
import socket
import sys
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlparse

import requests
from ddgs import DDGS  # type: ignore[import-not-found]
from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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
        logger.debug("Tor proxy check failed: %s", e)
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
        response = requests.get(
            "https://check.torproject.org/api/ip",
            proxies={"http": proxy, "https": proxy},
            timeout=timeout,
        )
        data = response.json()

        if not data.get("IsTor", False):
            logger.error("Traffic is NOT routing through Tor!")
            sys.exit("ERROR: Tor verification failed - traffic not going through Tor")

        return data.get("IP", "unknown")
    except requests.RequestException as e:
        logger.error("Failed to verify Tor connection: %s", e)
        sys.exit(f"ERROR: Could not verify Tor connection: {e}")


def check_privileges() -> None:
    """Warn if running with elevated privileges."""
    if os.name != "nt":
        if os.getuid() == 0:
            logger.warning("Running as root/admin is discouraged for security reasons")
    else:  # pyright: ignore[reportUnreachable]  # pragma: no cover
        # Windows admin check
        with suppress(AttributeError, OSError):
            import ctypes

            if ctypes.windll.shell32.IsUserAnAdmin():  # type: ignore[attr-defined]
                logger.warning(
                    "Running as Administrator is discouraged for security reasons"
                )


def print_privacy_status(proxy: str, exit_ip: str) -> None:
    """Display privacy status and recommendations at startup.

    Args:
        proxy: Active Tor proxy URL
        exit_ip: Verified Tor exit node IP
    """
    print()
    print("=" * 60)
    print("  SEARCHMCP - Privacy Mode ENABLED")
    print("=" * 60)
    print()
    print("  Privacy Checklist:")
    print(f"    [✓] Tor proxy: {proxy}")
    print(f"    [✓] Tor verified: exit IP {exit_ip}")
    print("    [✓] Query logging: DISABLED")
    print()
    print("  For Maximum Privacy, Also Use:")
    print("    • VPN (layered with Tor for defense in depth)")
    print("    • Privacy browser (Tor Browser, Brave, Firefox with")
    print("      privacy extensions, or LibreWolf)")
    print("    • Encrypted email (ProtonMail, Tutanota, or self-hosted)")
    print("    • Encrypted messaging (Signal, Session, or Matrix)")
    print("    • Privacy-respecting DNS (Quad9, Mullvad DNS, NextDNS)")
    print()
    print("  Threat Model Protection:")
    print("    • ISP surveillance: PROTECTED (Tor encryption)")
    print("    • Big Tech tracking: PROTECTED (no direct connection)")
    print("    • Network observers: PROTECTED (Tor routing)")
    print()
    print("=" * 60)
    print()


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
            SEARCHMCP_USE_TOR: Enable Tor routing (true/false/1/0/yes/no)
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
    logger.info(
        "Tor privacy mode ENABLED - all searches will route through %s",
        _tor_config.proxy,
    )
else:  # pragma: no cover
    logger.info("Tor privacy mode disabled - searches will use direct connection")


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
    _ddgs_client = None  # invalidate cached client so new config takes effect
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


def _validate_search_params(
    query: str,
    max_results: int,
    safe_search: Literal["off", "moderate", "strict"] | None = None,
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
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
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
        if _with_logging:
            logger.info("Web search: %s", query)
        else:
            logger.info("Web search performed (query content hidden for privacy)")
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
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
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
        if _with_logging:
            logger.info("Image search: %s", query)
        else:
            logger.info("Image search performed (query content hidden for privacy)")
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
        if _with_logging:
            logger.info("News search: %s", query)
        else:
            logger.info("News search performed (query content hidden for privacy)")
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
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
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
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
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
