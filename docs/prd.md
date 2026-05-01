# start docs/prd.md
# Product Requirements Document: searchmcp

## Overview

**searchmcp** is a Privacy-First Web Search MCP (Model Context Protocol) Server that provides web search capabilities to AI assistants using FastMCP and DuckDuckGo. All searches route through Tor by default for maximum privacy. The server also ships as a standalone Typer CLI, making it useful both as an MCP tool and as a direct command-line search utility.

## Purpose

Enable AI assistants to perform real-time web, image, news, video, and book searches through a standardized MCP interface without requiring API keys, while protecting user privacy from surveillance.

## Target Environment

- **Python Version**: 3.12+
- **Platform**: macOS (primary), Linux, Windows
- **Package Manager**: uv
- **Privacy**: Tor required (enabled by default)

## Privacy-by-Default Design

### Threat Model

SearchMCP protects against:
- **ISP surveillance**: All traffic is Tor-encrypted
- **Big Tech tracking**: No direct connection to search providers
- **Network observers**: Tor routing hides your IP
- **Query logging**: Search content is not logged by default

### Default Behavior

| Feature | Default | Override |
|---------|---------|----------|
| Tor routing | ENABLED | `--disable-privacy` or `SEARCHMCP_USE_TOR=false` |
| Query logging | DISABLED | `--with-logging` |
| Tor verification | Required at startup | N/A |

### CLI Flags

| Flag | Description |
|------|-------------|
| `--disable-privacy` | Bypass Tor, use direct connection (not recommended) |
| `--with-logging` | Enable query content in logs (disabled for privacy) |

## Core Features

### Common Parameters (All Search Tools)

All six MCP tools and all five search CLI subcommands share the following parameter set, defined by the `SearchParams` Pydantic model:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | str | required | Search query string |
| max_results | int | 10 | Maximum results (1-100) |
| region | str | "wt-wt" | Region code (worldwide) |
| safe_search | str | "moderate" | Safety filter (off/moderate/strict) |
| timelimit | str or None | None | Time window: d (day), w (week), m (month), y (year) |
| backend | str | "auto" | Search engine backend: single name, comma-separated list, "auto", or "all" |
| page | int | 1 | Result page number (1-100) |

The `SearchParams` Pydantic model (`searchmcp.params.SearchParams`) validates and freezes all parameters before they reach the search layer. Extra fields are ignored; unknown `safesearch` or `timelimit` values are rejected.

### 1. Web Search (`web_search`)

Search the web using DuckDuckGo's text search.

**Parameters:** See Common Parameters above.

**Returns:** List of results with title, href, and body fields.

### 2. Image Search (`image_search`)

Search for images using DuckDuckGo's image search.

**Parameters:** See Common Parameters above.

**Returns:** List of results with title, image, thumbnail, url, height, width, and source fields.

### 3. News Search (`news_search`)

Search for news articles using DuckDuckGo's news search.

**Parameters:** See Common Parameters above.

**Behavior change from previous version:** `safe_search` was previously omitted from `news_search`. It is now exposed on this tool, consistent with all other search tools. Clients that relied on the absence of this parameter should now pass `safe_search="moderate"` (the default) or the appropriate value explicitly.

**Returns:** List of results with title, url, body, date, image, and source fields.

### 4. Video Search (`videos_search`)

Search for videos using DuckDuckGo's video search.

**Parameters:** See Common Parameters above.

**Returns:** List of results with title, content, description, duration, embed_html, embed_url, image_token, images, provider, published, publisher, statistics, and uploader fields.

### 5. Books Search (`books_search`)

Search for books using DuckDuckGo. DuckDuckGo routes book queries through Anna's Archive, providing access to a broad catalog of academic, technical, and general-audience titles.

**Parameters:** See Common Parameters above.

**Returns:** List of results with title, author, publisher, info, url, and thumbnail fields.

## Typer CLI

SearchMCP ships as a dual-mode application: it functions as both an MCP server (for use with Claude Desktop, Cursor, and other MCP clients) and a standalone command-line tool for direct use in a terminal.

### Subcommands

| Subcommand | Description |
|------------|-------------|
| `searchmcp serve` | Start the MCP server (also the default when no subcommand is given) |
| `searchmcp web <query>` | Run a web search and display results |
| `searchmcp news <query>` | Run a news search and display results |
| `searchmcp images <query>` | Run an image search and display results |
| `searchmcp videos <query>` | Run a video search and display results |
| `searchmcp books <query>` | Run a book search and display results |

All search subcommands accept the common search flags (`--max-results`, `--region`, `--safesearch`, `--timelimit`, `--backend`, `--page`) as well as the privacy flags (`--disable-privacy`, `--with-logging`) and an output format flag (`--json` for raw JSON, default is a rich terminal table).

### CLI Usage Examples

```bash
# Start the MCP server (Tor required by default)
searchmcp serve

# Search the web, display a rich table
searchmcp web "python async patterns"

# Search for news, limit to last week, output JSON
searchmcp news "AI regulation" --timelimit w --json

# Search for images with a specific backend
searchmcp images "neural network diagrams" --backend bing

# Search for videos without Tor (not recommended)
searchmcp videos "fastmcp tutorial" --disable-privacy

# Search for books on a topic
searchmcp books "distributed systems"

# Paginate results (page 2)
searchmcp web "machine learning" --page 2 --max-results 20
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastmcp | >=3.0.0b1 | MCP server framework |
| ddgs | >=7.0.0 | DuckDuckGo search library |
| pydantic | >=2.0 | Search parameter validation model |
| httpx[socks] | >=0.27 | HTTP client with SOCKS proxy for Tor verification |
| typer | >=0.12 | CLI framework |
| structlog | >=24 | Structured logging |
| rich | >=13 | Terminal output formatting |
| orjson | >=3.10 | Fast JSON serialization |
| stamina | >=24 | Retry/resilience utilities |

## Tor Privacy Feature

### Overview

Tor routing is **enabled by default** for privacy-first operation. All searches route through the Tor network, hiding your IP address from DuckDuckGo and protecting your search queries from network surveillance.

### Startup Verification

On startup, SearchMCP:
1. Checks if Tor proxy is reachable
2. Verifies traffic routes through Tor via `check.torproject.org/api/ip`
3. Displays privacy status and exit node IP
4. Fails with clear error if Tor is unavailable

### Configuration

Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARCHMCP_USE_TOR` | `true` | Enable Tor routing (`true`/`false`/`1`/`0`/`yes`/`no`) |
| `SEARCHMCP_TOR_PROXY` | `socks5h://127.0.0.1:9050` | Tor SOCKS proxy URL |
| `SEARCHMCP_TOR_TIMEOUT` | `30` | Request timeout in seconds |

### Prerequisites

Tor must be running locally:
- **Tor service**: Port 9050 (install via `brew install tor && tor`)
- **Tor Browser**: Port 9150 (when Tor Browser is running)

### Usage Examples

```bash
# Default: Privacy enabled (requires Tor)
searchmcp serve

# Disable privacy (not recommended)
searchmcp serve --disable-privacy

# Enable query logging for debugging
searchmcp serve --with-logging

# Use Tor Browser instead of Tor service
SEARCHMCP_TOR_PROXY=socks5h://127.0.0.1:9150 searchmcp serve
```

### MCP Client Configuration with Tor

```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "searchmcp",
      "args": ["serve"]
    }
  }
}
```

Note: Tor is enabled by default, no special configuration needed.

### Privacy Notes

- Uses `socks5h://` protocol to ensure DNS queries also go through Tor
- All search types (web, image, news, videos, books) use Tor when enabled
- Setting applies to entire session, not individual queries
- Longer timeout (30s default) accommodates Tor network latency
- Query content is NOT logged by default

### Privacy Ecosystem Recommendations

For maximum privacy, also use:
- **VPN**: Layer with Tor for defense in depth
- **Privacy Browser**: Tor Browser, Brave, LibreWolf, or Firefox with privacy extensions
- **Encrypted Email**: ProtonMail, Tutanota, or self-hosted
- **Encrypted Messaging**: Signal, Session, or Matrix
- **Privacy DNS**: Quad9, Mullvad DNS, or NextDNS

### Rate Limiting Considerations

Tor exit nodes may be rate-limited by DuckDuckGo. If experiencing issues:
- Increase timeout via `SEARCHMCP_TOR_TIMEOUT`
- Restart Tor to get a new circuit/exit node
- Consider using Tor Browser which handles circuit rotation

## Non-Functional Requirements

### Performance
- Search responses should complete within 30 seconds through Tor
- Support concurrent requests

### Reliability
- Graceful error handling for network failures
- Input validation for all parameters via Pydantic `SearchParams` model
- Logging for debugging (without exposing queries by default)

### Security
- No API keys stored in code
- Safe search enabled by default
- No user data persistence
- No query logging by default
- Root/admin privilege warning

## Integration

Configure in your MCP client (e.g., Claude Desktop) by adding to the MCP servers configuration:

```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "searchmcp",
      "args": ["serve"]
    }
  }
}
```

## Success Criteria

1. All five search tools return valid results for standard queries
2. Error handling provides meaningful error messages
3. Input validation prevents invalid parameter values
4. All quality gates pass (ruff, mypy, pytest, bandit)
5. Test coverage > 80%
6. Privacy mode enabled and verified by default
7. Tor verification at startup
8. No query content in logs by default
9. CLI subcommands produce correct output in both table and JSON modes

## Future Enhancements

- Maps/places search
- Instant answers support
- Caching for repeated queries (with privacy considerations)
- Rate limiting protection
- Multiple Tor circuit support
# end docs/prd.md
