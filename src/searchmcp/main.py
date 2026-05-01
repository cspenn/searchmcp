"""Entry point for the searchmcp CLI and MCP server."""

from searchmcp.cli import app


def main() -> None:
    """Launch the searchmcp Typer CLI."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
