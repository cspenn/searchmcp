# start docs/prd.md
# Product Requirements Document: searchmcp

## Overview

**searchmcp** is a Web Search MCP (Model Context Protocol) Server that provides web search capabilities to AI assistants using FastMCP and DuckDuckGo.

## Purpose

Enable AI assistants to perform real-time web searches, image searches, and news searches through a standardized MCP interface without requiring API keys.

## Target Environment

- **Python Version**: 3.11+
- **Platform**: macOS (primary), Linux, Windows
- **Package Manager**: uv

## Core Features

### 1. Web Search (`web_search`)
Search the web using DuckDuckGo's text search.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | str | required | Search query string |
| max_results | int | 10 | Maximum results (1-100) |
| region | str | "wt-wt" | Region code (worldwide) |
| safe_search | str | "moderate" | Safety filter (off/moderate/strict) |

**Returns:** List of results with title, href, and body fields.

### 2. Image Search (`image_search`)
Search for images using DuckDuckGo's image search.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | str | required | Search query string |
| max_results | int | 10 | Maximum results (1-100) |
| region | str | "wt-wt" | Region code (worldwide) |
| safe_search | str | "moderate" | Safety filter (off/moderate/strict) |

**Returns:** List of results with title, image, thumbnail, url, and source fields.

### 3. News Search (`news_search`)
Search for news articles using DuckDuckGo's news search.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | str | required | Search query string |
| max_results | int | 10 | Maximum results (1-100) |
| region | str | "wt-wt" | Region code (worldwide) |

**Returns:** List of results with title, url, body, date, and source fields.

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastmcp | >=2.0.0 | MCP server framework |
| ddgs | >=7.0.0 | DuckDuckGo search library |
| pysocks | >=1.7.1 | SOCKS proxy support for Tor |

## Tor Privacy Feature

### Overview

Optional Tor routing for enhanced privacy. When enabled, all searches in a session are routed through the Tor network, hiding the user's IP address from DuckDuckGo.

### Configuration

Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARCHMCP_USE_TOR` | `false` | Enable Tor routing (`true`/`false`/`1`/`0`/`yes`/`no`) |
| `SEARCHMCP_TOR_PROXY` | `socks5h://127.0.0.1:9050` | Tor SOCKS proxy URL |
| `SEARCHMCP_TOR_TIMEOUT` | `30` | Request timeout in seconds |

### Prerequisites

Tor must be running locally:
- **Tor service**: Port 9050 (install via `brew install tor && tor`)
- **Tor Browser**: Port 9150 (when Tor Browser is running)

### Usage Examples

```bash
# Enable Tor with default settings (Tor service on port 9050)
SEARCHMCP_USE_TOR=true python server.py

# Enable Tor with Tor Browser (port 9150)
SEARCHMCP_USE_TOR=true SEARCHMCP_TOR_PROXY=socks5h://127.0.0.1:9150 python server.py
```

### MCP Client Configuration with Tor

```json
{
  "mcpServers": {
    "searchmcp-tor": {
      "command": "python",
      "args": ["/path/to/searchmcp/server.py"],
      "env": {
        "SEARCHMCP_USE_TOR": "true"
      }
    }
  }
}
```

### Privacy Notes

- Uses `socks5h://` protocol to ensure DNS queries also go through Tor
- All search types (web, image, news) use Tor when enabled
- Setting applies to entire session, not individual queries
- Longer timeout (30s default) accommodates Tor network latency

### Rate Limiting Considerations

Tor exit nodes may be rate-limited by DuckDuckGo. If experiencing issues:
- Increase timeout via `SEARCHMCP_TOR_TIMEOUT`
- Restart Tor to get a new circuit/exit node
- Consider using Tor Browser which handles circuit rotation

## Non-Functional Requirements

### Performance
- Search responses should complete within 5 seconds under normal network conditions
- Support concurrent requests

### Reliability
- Graceful error handling for network failures
- Input validation for all parameters
- Logging for debugging and monitoring

### Security
- No API keys stored in code
- Safe search enabled by default
- No user data persistence

## Usage

```bash
# Run the MCP server
python -m searchmcp.main

# Or directly
python server.py
```

## Integration

Configure in your MCP client (e.g., Claude Desktop) by adding to the MCP servers configuration:

```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "python",
      "args": ["/path/to/searchmcp/server.py"]
    }
  }
}
```

## Success Criteria

1. All three search tools return valid results for standard queries
2. Error handling provides meaningful error messages
3. Input validation prevents invalid parameter values
4. All quality gates pass (ruff, mypy, pytest, bandit)
5. Test coverage > 80%

## Future Enhancements

- Video search support
- Maps/places search
- Instant answers support
- Caching for repeated queries
- Rate limiting protection
# end docs/prd.md
