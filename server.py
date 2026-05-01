# start server.py
"""Backwards-compat shim - keeps `fastmcp dev server.py` and existing MCP client configs working."""

from searchmcp.main import main

if __name__ == "__main__":
    main()
# end server.py
