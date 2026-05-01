"""Entry point shim: re-exports main and mcp for `python server.py` and `fastmcp dev server.py`."""

from searchmcp.main import main
from searchmcp.server import mcp  # noqa: F401  (discovered by `fastmcp dev`)

if __name__ == "__main__":
    main()
