"""Typer CLI for searchmcp: privacy-first search and MCP server launcher."""

import json
import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from searchmcp.params import SearchParams
from searchmcp.server import (
    TorConfig,
    check_privileges,
    configure,
    mcp,
    print_privacy_status,
    verify_tor_proxy,
    verify_tor_exit,
)

app = typer.Typer(
    name="searchmcp",
    help="Privacy-first search CLI and MCP server (routes searches through Tor by default).",
    invoke_without_command=True,
    no_args_is_help=False,
)

_console = Console()


def startup_privacy_check(disable_privacy: bool, config: TorConfig) -> None:
    """Perform startup privacy verification.

    Args:
        disable_privacy: Whether privacy mode was explicitly disabled.
        config: Active Tor configuration after configure() was called.

    Raises:
        SystemExit: If Tor is required but unavailable.
    """
    check_privileges()

    if disable_privacy:
        typer.echo(
            "WARNING: Privacy mode disabled. Your searches are NOT private.", err=True
        )
        typer.echo("", err=True)
        return

    if not verify_tor_proxy(config.proxy):
        sys.exit(
            f"ERROR: Cannot connect to Tor proxy at {config.proxy}\n"
            "Please ensure Tor is running:\n"
            "  macOS:  brew install tor && tor\n"
            "  Linux:  sudo apt install tor && sudo systemctl start tor\n"
            "  Or run with --disable-privacy (not recommended)"
        )

    exit_ip = verify_tor_exit(config.proxy, config.timeout)
    print_privacy_status(config.proxy, exit_ip)


def _apply_config(disable_privacy: bool, with_logging: bool) -> TorConfig:
    """Apply CLI flags to global server config and return active TorConfig.

    Args:
        disable_privacy: Disable Tor routing when True.
        with_logging: Enable query content in logs when True.

    Returns:
        The active TorConfig after applying settings.
    """
    tor_config: TorConfig | None = (
        TorConfig(enabled=False, proxy="", timeout=30) if disable_privacy else None
    )
    return configure(with_logging=with_logging, tor_config=tor_config)


def _display_results(results: list[dict], as_json: bool) -> None:
    """Render search results to stdout as a rich table or JSON.

    Args:
        results: List of result dicts from a do_*_search call.
        as_json: Output raw JSON when True; rich table when False.
    """
    if as_json:
        typer.echo(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if not results:
        typer.echo("No results found.")
        return

    columns = list(results[0].keys())
    table = Table(show_header=True, header_style="bold")
    for col in columns:
        table.add_column(col, overflow="fold", max_width=60)
    for row in results:
        table.add_row(*[str(row.get(col, "")) for col in columns])
    _console.print(table)


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    disable_privacy: Annotated[
        bool,
        typer.Option("--disable-privacy", help="Disable Tor routing (not recommended)"),
    ] = False,
    with_logging: Annotated[
        bool,
        typer.Option("--with-logging", help="Enable query content in logs"),
    ] = False,
) -> None:
    """Privacy-first search CLI and MCP server.

    Run without a subcommand to start the MCP server (same as 'searchmcp serve').
    """
    if ctx.invoked_subcommand is None:
        _run_serve(disable_privacy=disable_privacy, with_logging=with_logging)


def _run_serve(disable_privacy: bool, with_logging: bool) -> None:
    """Start the MCP server after applying configuration and privacy checks."""
    active_config = _apply_config(disable_privacy, with_logging)
    startup_privacy_check(disable_privacy, active_config)
    mcp.run()


@app.command()
def serve(
    disable_privacy: Annotated[
        bool,
        typer.Option("--disable-privacy", help="Disable Tor routing (not recommended)"),
    ] = False,
    with_logging: Annotated[
        bool,
        typer.Option("--with-logging", help="Enable query content in logs"),
    ] = False,
) -> None:
    """Start the MCP server for use with Claude, Cursor, and other MCP clients."""
    _run_serve(disable_privacy=disable_privacy, with_logging=with_logging)


def _run_search(  # noqa: PLR0913
    category: str,
    query: str,
    disable_privacy: bool,
    with_logging: bool,
    max_results: int,
    region: str,
    safe_search: str,
    timelimit: str | None,
    backend: str,
    page: int,
    as_json: bool,
) -> None:
    """Shared search execution logic for all search subcommands."""
    from searchmcp.server import (
        do_web_search,
        do_image_search,
        do_news_search,
        do_videos_search,
        do_books_search,
        SearchError,
    )

    _SEARCH_FNS = {
        "web": do_web_search,
        "images": do_image_search,
        "news": do_news_search,
        "videos": do_videos_search,
        "books": do_books_search,
    }

    active_config = _apply_config(disable_privacy, with_logging)
    startup_privacy_check(disable_privacy, active_config)

    params = SearchParams(
        max_results=max_results,
        region=region,
        safesearch=safe_search,  # type: ignore[arg-type]
        timelimit=timelimit,  # type: ignore[arg-type]
        backend=backend,
        page=page,
    )

    try:
        results = _SEARCH_FNS[category](query, params)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except SearchError as e:
        typer.echo(f"Search failed: {e}", err=True)
        raise typer.Exit(code=1) from e

    _display_results(results, as_json)


@app.command()
def web(  # noqa: PLR0913
    query: Annotated[str, typer.Argument(help="Search query")],
    max_results: Annotated[
        int, typer.Option("--max-results", help="Results (1-100)")
    ] = 10,
    region: Annotated[
        str, typer.Option(help="Region code (wt-wt = worldwide)")
    ] = "wt-wt",
    safe_search: Annotated[
        str, typer.Option("--safesearch", help="Safety filter (off/moderate/strict)")
    ] = "moderate",
    timelimit: Annotated[
        str | None, typer.Option("--timelimit", help="Time limit (d/w/m/y)")
    ] = None,
    backend: Annotated[
        str, typer.Option(help="Backend engine(s) (auto/all/name or comma-separated)")
    ] = "auto",
    page: Annotated[int, typer.Option(help="Result page (1-100)")] = 1,
    disable_privacy: Annotated[
        bool, typer.Option("--disable-privacy", help="Disable Tor routing")
    ] = False,
    with_logging: Annotated[
        bool, typer.Option("--with-logging", help="Enable query content in logs")
    ] = False,
    as_json: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Search the web using DuckDuckGo."""
    _run_search(
        "web",
        query,
        disable_privacy,
        with_logging,
        max_results,
        region,
        safe_search,
        timelimit,
        backend,
        page,
        as_json,
    )


@app.command()
def news(  # noqa: PLR0913
    query: Annotated[str, typer.Argument(help="Search query")],
    max_results: Annotated[
        int, typer.Option("--max-results", help="Results (1-100)")
    ] = 10,
    region: Annotated[
        str, typer.Option(help="Region code (wt-wt = worldwide)")
    ] = "wt-wt",
    safe_search: Annotated[
        str, typer.Option("--safesearch", help="Safety filter (off/moderate/strict)")
    ] = "moderate",
    timelimit: Annotated[
        str | None, typer.Option("--timelimit", help="Time limit (d/w/m/y)")
    ] = None,
    backend: Annotated[
        str, typer.Option(help="Backend engine(s) (auto/all/name or comma-separated)")
    ] = "auto",
    page: Annotated[int, typer.Option(help="Result page (1-100)")] = 1,
    disable_privacy: Annotated[
        bool, typer.Option("--disable-privacy", help="Disable Tor routing")
    ] = False,
    with_logging: Annotated[
        bool, typer.Option("--with-logging", help="Enable query content in logs")
    ] = False,
    as_json: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Search for news articles using DuckDuckGo."""
    _run_search(
        "news",
        query,
        disable_privacy,
        with_logging,
        max_results,
        region,
        safe_search,
        timelimit,
        backend,
        page,
        as_json,
    )


@app.command()
def images(  # noqa: PLR0913
    query: Annotated[str, typer.Argument(help="Search query")],
    max_results: Annotated[
        int, typer.Option("--max-results", help="Results (1-100)")
    ] = 10,
    region: Annotated[
        str, typer.Option(help="Region code (wt-wt = worldwide)")
    ] = "wt-wt",
    safe_search: Annotated[
        str, typer.Option("--safesearch", help="Safety filter (off/moderate/strict)")
    ] = "moderate",
    timelimit: Annotated[
        str | None, typer.Option("--timelimit", help="Time limit (d/w/m/y)")
    ] = None,
    backend: Annotated[
        str, typer.Option(help="Backend engine(s) (auto/all/name or comma-separated)")
    ] = "auto",
    page: Annotated[int, typer.Option(help="Result page (1-100)")] = 1,
    disable_privacy: Annotated[
        bool, typer.Option("--disable-privacy", help="Disable Tor routing")
    ] = False,
    with_logging: Annotated[
        bool, typer.Option("--with-logging", help="Enable query content in logs")
    ] = False,
    as_json: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Search for images using DuckDuckGo."""
    _run_search(
        "images",
        query,
        disable_privacy,
        with_logging,
        max_results,
        region,
        safe_search,
        timelimit,
        backend,
        page,
        as_json,
    )


@app.command()
def videos(  # noqa: PLR0913
    query: Annotated[str, typer.Argument(help="Search query")],
    max_results: Annotated[
        int, typer.Option("--max-results", help="Results (1-100)")
    ] = 10,
    region: Annotated[
        str, typer.Option(help="Region code (wt-wt = worldwide)")
    ] = "wt-wt",
    safe_search: Annotated[
        str, typer.Option("--safesearch", help="Safety filter (off/moderate/strict)")
    ] = "moderate",
    timelimit: Annotated[
        str | None, typer.Option("--timelimit", help="Time limit (d/w/m/y)")
    ] = None,
    backend: Annotated[
        str, typer.Option(help="Backend engine(s) (auto/all/name or comma-separated)")
    ] = "auto",
    page: Annotated[int, typer.Option(help="Result page (1-100)")] = 1,
    disable_privacy: Annotated[
        bool, typer.Option("--disable-privacy", help="Disable Tor routing")
    ] = False,
    with_logging: Annotated[
        bool, typer.Option("--with-logging", help="Enable query content in logs")
    ] = False,
    as_json: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Search for videos using DuckDuckGo."""
    _run_search(
        "videos",
        query,
        disable_privacy,
        with_logging,
        max_results,
        region,
        safe_search,
        timelimit,
        backend,
        page,
        as_json,
    )


@app.command()
def books(  # noqa: PLR0913
    query: Annotated[str, typer.Argument(help="Search query")],
    max_results: Annotated[
        int, typer.Option("--max-results", help="Results (1-100)")
    ] = 10,
    region: Annotated[
        str, typer.Option(help="Region code (wt-wt = worldwide)")
    ] = "wt-wt",
    safe_search: Annotated[
        str, typer.Option("--safesearch", help="Safety filter (off/moderate/strict)")
    ] = "moderate",
    timelimit: Annotated[
        str | None, typer.Option("--timelimit", help="Time limit (d/w/m/y)")
    ] = None,
    backend: Annotated[
        str, typer.Option(help="Backend engine(s) (auto/all/name or comma-separated)")
    ] = "auto",
    page: Annotated[int, typer.Option(help="Result page (1-100)")] = 1,
    disable_privacy: Annotated[
        bool, typer.Option("--disable-privacy", help="Disable Tor routing")
    ] = False,
    with_logging: Annotated[
        bool, typer.Option("--with-logging", help="Enable query content in logs")
    ] = False,
    as_json: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Search for books using DuckDuckGo (via Anna's Archive)."""
    _run_search(
        "books",
        query,
        disable_privacy,
        with_logging,
        max_results,
        region,
        safe_search,
        timelimit,
        backend,
        page,
        as_json,
    )
