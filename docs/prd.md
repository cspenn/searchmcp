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
