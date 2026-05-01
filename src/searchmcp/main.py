# start src/searchmcp/main.py
"""Entry point orchestrator for searchmcp."""

import argparse
import logging
import sys

from searchmcp.server import (
    TorConfig,
    check_privileges,
    verify_tor_proxy,
    verify_tor_exit,
    print_privacy_status,
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="SearchMCP - Privacy-first web search via MCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Privacy is enabled by default. All searches route through Tor.

For maximum privacy:
  - Use a VPN in addition to Tor
  - Use a privacy-focused browser (Tor Browser, Brave, Firefox)
  - Use encrypted email (ProtonMail, Tutanota)
""",
    )
    parser.add_argument(
        "--disable-privacy",
        action="store_true",
        help="Disable Tor routing (not recommended - exposes your IP)",
    )
    parser.add_argument(
        "--with-logging",
        action="store_true",
        help="Enable query content in logs (disabled by default for privacy)",
    )
    return parser.parse_args()


def startup_privacy_check(args: argparse.Namespace, config: TorConfig) -> None:
    """Perform startup privacy verification.

    Args:
        args: Parsed command line arguments
        config: Tor configuration

    Raises:
        SystemExit: If privacy mode is enabled but Tor is unavailable.
    """
    check_privileges()

    if args.disable_privacy:
        logger.warning("Privacy mode DISABLED - searches will use direct connection")
        logger.warning("Your IP address will be visible to DuckDuckGo")
        print()
        print("WARNING: Privacy mode disabled. Your searches are NOT private.")
        print()
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


def main() -> None:
    """Main entry point with privacy checks."""
    import searchmcp.server as _server

    args = parse_args()

    _server._with_logging = args.with_logging

    if args.disable_privacy:
        _server._tor_config = TorConfig(
            enabled=False,
            proxy=_server._tor_config.proxy,
            timeout=_server._tor_config.timeout,
        )

    startup_privacy_check(args, _server._tor_config)
    _server.mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
# end src/searchmcp/main.py
