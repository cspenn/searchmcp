# SearchMCP - Private Web Search for AI

Privacy-first web search via Model Context Protocol. All searches route through
Tor by default, protecting your queries from surveillance.

## Why Privacy Matters

Every web search reveals your interests, concerns, health questions, political
views, and more. This data is collected by:

- **ISPs**: Your internet provider sees every search query
- **Big Tech**: Google, Microsoft, and others build detailed profiles
- **Governments**: Mass surveillance programs collect search data
- **Advertisers**: Your searches are sold to target you with ads

SearchMCP protects you by routing all searches through the Tor network,
making it impossible to trace queries back to you.

## What SearchMCP Does

SearchMCP is both a standalone CLI tool and an MCP (Model Context Protocol)
server that gives AI assistants privacy-preserving web search capability.
It exposes five tools:

- **`web_search`** — Full web search via DuckDuckGo
- **`image_search`** — Image search via DuckDuckGo
- **`news_search`** — News article search via DuckDuckGo
- **`videos_search`** — Video search via DuckDuckGo
- **`books_search`** — Book search via DuckDuckGo

All traffic routes through Tor by default. Query content is never logged.
Privacy verification runs at startup to confirm your searches are actually
going through Tor before the server accepts any requests.

## Prerequisites

### 1. Tor Service (Required)

Tor must be running locally for SearchMCP to work.

**macOS:**
```bash
brew install tor
tor  # Runs in foreground, or use 'brew services start tor' for background
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install tor
sudo systemctl start tor
sudo systemctl enable tor  # Start on boot
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install tor
sudo systemctl start tor
sudo systemctl enable tor
```

**Windows:**
Download and run the Tor Expert Bundle from https://www.torproject.org/download/tor/

**Alternative: Tor Browser**

If you have Tor Browser installed, it provides a Tor proxy on port 9150:
```bash
SEARCHMCP_TOR_PROXY=socks5h://127.0.0.1:9150 searchmcp
```

### 2. VPN (Recommended)

For defense in depth, use a VPN alongside Tor:

- **Mullvad VPN**: No account needed, privacy-focused
- **ProtonVPN**: From the ProtonMail team
- **IVPN**: Strong privacy policy

Connect to VPN first, then start Tor. This hides Tor usage from your ISP.

## Installation

SearchMCP is packaged as a standard Python package that installs a `searchmcp`
command available system-wide. Use it as a standalone CLI tool or configure it
as an MCP server for Claude, Cursor, and other MCP clients.

**From PyPI (recommended):**
```bash
# With uv (recommended)
uv add searchmcp

# Or with pip
pip install searchmcp
```

**From source with [uv](https://docs.astral.sh/uv/):**
```bash
# Clone the repository
git clone https://github.com/cspenn/searchmcp.git
cd searchmcp

# Install as a tool (adds `searchmcp` to your PATH)
uv tool install .
```

**Alternative: editable install in a project venv**

If the consuming project has its own virtualenv and you want changes in the
checkout reflected immediately:

```bash
uv pip install -e /path/to/searchmcp
```

## Quick Start

1. **Start Tor** (see Prerequisites above)

2. **Run SearchMCP as an MCP server** (for Claude, Cursor, etc.):
   ```bash
   searchmcp serve
   # or simply:
   searchmcp
   ```

   **Or run a one-off CLI search directly:**
   ```bash
   searchmcp web "privacy tools 2025"
   searchmcp news "AI regulation" --timelimit w --max-results 5
   searchmcp images "Tor network diagram"
   searchmcp videos "how to use Tor browser"
   searchmcp books "digital privacy handbook"
   ```

3. **Verify privacy status** in the startup output:
   ```
   ============================================================
     SEARCHMCP - Privacy Mode ENABLED
   ============================================================

     Privacy Checklist:
       [✓] Tor proxy: socks5h://127.0.0.1:9050
       [✓] Tor verified: exit IP 185.220.101.x
       [✓] Query logging: DISABLED

     For Maximum Privacy, Also Use:
       • VPN (layered with Tor for defense in depth)
       • Privacy browser (Tor Browser, Brave, Firefox with
         privacy extensions, or LibreWolf)
       • Encrypted email (ProtonMail, Tutanota, or self-hosted)
       • Encrypted messaging (Signal, Session, or Matrix)
       • Privacy-respecting DNS (Quad9, Mullvad DNS, NextDNS)
   ```

## Privacy Features

| Feature | Default | Description |
|---------|---------|-------------|
| Tor routing | ON | All searches go through Tor |
| Query logging | OFF | Your searches are never recorded |
| DNS leak prevention | ON | Uses socks5h:// protocol |
| Exit verification | ON | Confirms Tor connection at startup |

## CLI Reference

SearchMCP provides six subcommands. Running `searchmcp` with no subcommand
is equivalent to `searchmcp serve`.

### `serve` — Start the MCP server

```
searchmcp serve [--disable-privacy] [--with-logging]
```

| Flag | Description |
|------|-------------|
| `--disable-privacy` | Disable Tor routing (not recommended) |
| `--with-logging` | Enable query content in logs for debugging |

**Examples:**
```bash
# Default: Maximum privacy
searchmcp serve

# Debugging with query logging (use cautiously)
searchmcp serve --with-logging

# Disable privacy mode (not recommended)
searchmcp serve --disable-privacy
```

### Search subcommands

All five search subcommands share the same flag surface:

```
searchmcp web    QUERY [options]
searchmcp news   QUERY [options]
searchmcp images QUERY [options]
searchmcp videos QUERY [options]
searchmcp books  QUERY [options]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--max-results N` | 10 | Number of results to return (1-100) |
| `--region R` | `wt-wt` | Region code (`wt-wt` = worldwide; e.g. `us-en`, `uk-en`) |
| `--safesearch S` | `moderate` | Safety filter: `off`, `moderate`, or `strict` |
| `--timelimit T` | (none) | Time window: `d` (day), `w` (week), `m` (month), `y` (year) |
| `--backend B` | `auto` | Backend engine(s): `auto`, `all`, or a name / comma-separated list |
| `--page P` | 1 | Result page number (1-100) |
| `--disable-privacy` | off | Disable Tor routing (not recommended) |
| `--with-logging` | off | Log query content (use cautiously) |
| `--json` | off | Output raw JSON instead of a formatted table |

**Examples:**
```bash
# Web search — default settings
searchmcp web "open source privacy tools"

# News from the past week, JSON output
searchmcp news "AI regulation" --timelimit w --max-results 20 --json

# UK image search with strict safe-search
searchmcp images "data center" --region uk-en --safesearch strict

# Video search, second page of results
searchmcp videos "Tor browser tutorial" --page 2

# Book search with JSON output
searchmcp books "surveillance capitalism" --json
```

## Configuration

Environment variables for advanced users:

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARCHMCP_USE_TOR` | `true` | Enable/disable Tor (`true`/`false`) |
| `SEARCHMCP_TOR_PROXY` | `socks5h://127.0.0.1:9050` | Tor proxy address |
| `SEARCHMCP_TOR_TIMEOUT` | `30` | Request timeout in seconds |

**Example:**
```bash
# Use Tor Browser's proxy
SEARCHMCP_TOR_PROXY=socks5h://127.0.0.1:9150 searchmcp

# Increase timeout for slow connections
SEARCHMCP_TOR_TIMEOUT=60 searchmcp
```

## MCP Client Configuration

Because `searchmcp` is installed as a console script on your PATH, the
configuration is the same for every MCP client — no path hard-coding needed.

```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "searchmcp"
    }
  }
}
```

See the **LLM Installation Assistant** section below for client-specific
instructions (Claude Desktop, Claude Code, Cursor, VS Code, LM Studio, etc.).

## Comprehensive Privacy Setup

SearchMCP protects your searches, but for comprehensive privacy, consider your
entire digital footprint:

### Web Browsers

| Browser | Privacy Level | Notes |
|---------|--------------|-------|
| **Tor Browser** | Highest | Routes all traffic through Tor |
| **LibreWolf** | Very High | Hardened Firefox fork |
| **Brave** | High | Built-in Tor mode, ad blocking |
| **Firefox** | Medium-High | Requires manual hardening |

**Firefox Privacy Extensions:**
- uBlock Origin (ad/tracker blocking)
- Privacy Badger (tracker learning)
- HTTPS Everywhere (force encryption)
- NoScript (JavaScript control)
- Container Tabs (isolate sites)

### Email

| Service | Privacy Level | Notes |
|---------|--------------|-------|
| **ProtonMail** | Very High | End-to-end encrypted, Swiss jurisdiction |
| **Tutanota** | Very High | End-to-end encrypted, German jurisdiction |
| **Mailbox.org** | High | Privacy-focused, German jurisdiction |
| **Self-hosted** | Highest | Full control, requires expertise |

**Avoid:** Gmail, Outlook, Yahoo (scan and monetize your emails)

### Messaging

| App | Privacy Level | Notes |
|-----|--------------|-------|
| **Signal** | Very High | Gold standard for secure messaging |
| **Session** | Very High | No phone number required, decentralized |
| **Matrix/Element** | High | Decentralized, self-hostable |
| **Briar** | Very High | Peer-to-peer, works without internet |

**Avoid:** WhatsApp (Meta), Telegram (unencrypted by default), SMS

### DNS

Your DNS queries reveal every site you visit. Use encrypted DNS:

| Service | Privacy Level | Notes |
|---------|--------------|-------|
| **Quad9** | Very High | Blocks malware, privacy-focused |
| **Mullvad DNS** | Very High | No logging, from VPN provider |
| **NextDNS** | High | Customizable, some logging |
| **Cloudflare (1.1.1.1)** | Medium | Fast, but Cloudflare sees queries |

### Operating Systems

| OS | Privacy Level | Notes |
|----|--------------|-------|
| **Tails** | Highest | Live OS, routes all traffic through Tor |
| **Whonix** | Very High | VM-based Tor routing |
| **Qubes OS** | Very High | Security through compartmentalization |
| **Linux** | High | Avoid Ubuntu (telemetry), use Fedora/Debian |

**Avoid:** Windows (extensive telemetry), macOS (some telemetry)

### Search Engines

| Engine | Privacy Level | Notes |
|--------|--------------|-------|
| **DuckDuckGo** | High | No tracking, used by SearchMCP |
| **Startpage** | High | Google results without tracking |
| **Searx** | Very High | Self-hostable metasearch |
| **Brave Search** | High | Independent index |

**Avoid:** Google, Bing, Yahoo (track everything)

## Development

### Hot Reload with MCP Inspector

FastMCP v3 provides a development server with hot reload and an interactive inspector:

```bash
uv run fastmcp dev server.py
```

This opens a browser-based MCP Inspector where you can:
- Test tools interactively
- View tool schemas
- Debug request/response payloads

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ -v --cov=src/searchmcp --cov-report=term-missing

# Run only unit tests (skip integration tests requiring Tor)
uv run pytest tests/ -v -m "not integration"
```

### Code Quality

```bash
# Type checking
uv run mypy src/

# Linting
uv run ruff check src/

# Format code
uv run ruff format src/
```

## Troubleshooting

### "Cannot connect to Tor proxy"

**Cause:** Tor service is not running.

**Solution:**
```bash
# macOS
tor  # or: brew services start tor

# Linux
sudo systemctl start tor

# Check if Tor is running
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip
```

### "Tor verification failed"

**Cause:** Tor is running but not routing traffic correctly.

**Solution:**
1. Restart Tor: `sudo systemctl restart tor`
2. Check Tor logs: `journalctl -u tor`
3. Verify firewall allows Tor connections

### Slow searches

**Cause:** Normal. Tor adds latency for privacy.

**Solutions:**
- Increase timeout: `SEARCHMCP_TOR_TIMEOUT=60 searchmcp`
- Tor is typically 2-5x slower than direct connections
- Consider this the cost of privacy

### Rate limiting

**Cause:** DuckDuckGo rate-limits Tor exit nodes.

**Solutions:**
- Wait a few minutes and retry
- Restart Tor to get a new exit node: `sudo systemctl restart tor`
- Increase timeout for retries

## Security Best Practices

1. **Always use VPN + Tor** for maximum privacy
2. **Don't run as root/admin** - SearchMCP will warn you
3. **Don't use `--with-logging` in production** - logs your queries
4. **Keep Tor updated** - `brew upgrade tor` or `apt upgrade tor`
5. **Use privacy browser** for following search result links
6. **Compartmentalize** - don't mix anonymous and identified activities

## API Reference

### MCP Tools

SearchMCP exposes five MCP tools. All tools accept the same parameter set.

#### Common parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | (required) | Search query |
| `max_results` | `int` | `10` | Number of results (1-100) |
| `region` | `str` | `"wt-wt"` | Region code (`wt-wt` = worldwide) |
| `safe_search` | `str` | `"moderate"` | Safety filter: `off`, `moderate`, or `strict` |
| `timelimit` | `str \| None` | `None` | Time window: `d`, `w`, `m`, or `y` |
| `backend` | `str` | `"auto"` | Backend engine(s): `auto`, `all`, or a name |
| `page` | `int` | `1` | Result page (1-100) |

#### `web_search`
```python
web_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
    timelimit: Literal["d", "w", "m", "y"] | None = None,
    backend: str = "auto",
    page: int = 1,
) -> list[dict]
# Returns: title, href, body
```

#### `image_search`
```python
image_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
    timelimit: Literal["d", "w", "m", "y"] | None = None,
    backend: str = "auto",
    page: int = 1,
) -> list[dict]
# Returns: title, image, thumbnail, url, height, width, source
```

#### `news_search`
```python
news_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
    timelimit: Literal["d", "w", "m", "y"] | None = None,
    backend: str = "auto",
    page: int = 1,
) -> list[dict]
# Returns: title, url, body, date, image, source
```

#### `videos_search`
```python
videos_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
    timelimit: Literal["d", "w", "m", "y"] | None = None,
    backend: str = "auto",
    page: int = 1,
) -> list[dict]
# Returns: title, content, description, duration, embed_html, embed_url,
#          image_token, images, provider, published, publisher, statistics, uploader
```

#### `books_search`
```python
books_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: Literal["off", "moderate", "strict"] = "moderate",
    timelimit: Literal["d", "w", "m", "y"] | None = None,
    backend: str = "auto",
    page: int = 1,
) -> list[dict]
# Returns: title, author, publisher, info, url, thumbnail
```

### Python Library API

SearchMCP can also be used as a Python library. All five functions accept a
query string and an optional `SearchParams` object.

```python
from searchmcp.server import (
    do_web_search,
    do_image_search,
    do_news_search,
    do_videos_search,
    do_books_search,
)
from searchmcp.params import SearchParams

params = SearchParams(
    max_results=20,
    region="us-en",
    safesearch="moderate",
    timelimit="w",   # past week
    backend="auto",
    page=1,
)

results = do_web_search("open source privacy tools", params)
for r in results:
    print(r["title"], r["href"])

# All functions share the same signature:
# do_web_search(query: str, params: SearchParams | None = None) -> list[dict]
# do_image_search(query: str, params: SearchParams | None = None) -> list[dict]
# do_news_search(query: str, params: SearchParams | None = None) -> list[dict]
# do_videos_search(query: str, params: SearchParams | None = None) -> list[dict]
# do_books_search(query: str, params: SearchParams | None = None) -> list[dict]
```

`SearchParams` fields:

| Field | Type | Default | Constraint |
|-------|------|---------|------------|
| `max_results` | `int` | `10` | 1-100 |
| `region` | `str` | `"wt-wt"` | DuckDuckGo region code |
| `safesearch` | `str` | `"moderate"` | `off`, `moderate`, or `strict` |
| `timelimit` | `str \| None` | `None` | `d`, `w`, `m`, or `y` |
| `backend` | `str` | `"auto"` | `auto`, `all`, or engine name |
| `page` | `int` | `1` | 1-100 |

---

## LLM Installation Assistant

The following prompt can be given to any LLM (Claude, ChatGPT, etc.) to help you install and configure SearchMCP:

<details>
<summary>Click to expand installation prompt</summary>

```
You are helping a user install SearchMCP, a privacy-first web search MCP server that routes all searches through Tor.

## Your Task
Guide the user through installing SearchMCP step by step. Ask questions to understand their setup, then provide specific commands and configuration.

## Step 1: Gather Information

Ask the user these questions (you can ask multiple at once):

1. **Operating System**: Are you using macOS, Linux (which distro?), or Windows?
2. **MCP Client**: Which MCP client do you use?
   - Claude Desktop
   - Claude Code (CLI)
   - VS Code with Cline extension
   - VS Code with Continue extension
   - Cursor
   - LM Studio
   - AnythingLLM
   - Qwen Code
   - Other (ask which one)
3. **uv**: Do you have uv installed? (Check with `uv --version`)
4. **Tor**: Do you have Tor installed? (Check with `tor --version`)

## Step 2: Install Prerequisites

Based on their OS, provide the appropriate commands:

### uv

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Tor

**macOS:**
```bash
brew install tor
brew services start tor  # Run in background
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt update && sudo apt install tor
sudo systemctl start tor
sudo systemctl enable tor
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install tor
sudo systemctl start tor
sudo systemctl enable tor
```

**Windows:**
Download Tor Expert Bundle from https://www.torproject.org/download/tor/
Extract and run tor.exe

## Step 3: Install SearchMCP

```bash
# Clone the repository
git clone https://github.com/cspenn/searchmcp.git
cd searchmcp

# Install as a tool -- adds `searchmcp` to your PATH
uv tool install .
```

Verify the install worked:
```bash
searchmcp --help
```

## Step 4: Configure MCP Client

Because `searchmcp` is on the user's PATH, the configuration is simple and identical across all clients:

```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "searchmcp"
    }
  }
}
```

Based on their MCP client, show them where to put it:

### Claude Desktop

**Config file location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "searchmcp"
    }
  }
}
```

If they already have other MCP servers configured, help them merge the configuration.

### Claude Code (CLI)

**Option 1: CLI command (recommended):**
```bash
claude mcp add --transport stdio --scope user searchmcp -- searchmcp
```

**Option 2: Edit config file directly:**

Config file: `~/.claude.json`

```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "searchmcp"
    }
  }
}
```

**Verify installation:** Use `/mcp` command within Claude Code to check server status.

**Scopes:**
- `--scope user`: Available across all projects (recommended)
- `--scope local`: Only in current project
- `--scope project`: Shared via `.mcp.json` file

### VS Code with Cline

**Config location:** VS Code Settings > Cline > MCP Servers

Or add to `.vscode/mcp.json` in their workspace:
```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "searchmcp"
    }
  }
}
```

### VS Code with Continue

**Config location:** `~/.continue/config.json`

Add to the experimental MCP servers section:
```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": {
          "type": "stdio",
          "command": "searchmcp"
        }
      }
    ]
  }
}
```

### Cursor

**Config location:** Cursor Settings > MCP

```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "searchmcp"
    }
  }
}
```

### LM Studio

**Config file location:**
- macOS/Linux: `~/.lmstudio/mcp.json`
- Windows: `%USERPROFILE%\.lmstudio\mcp.json`

**To edit:** Open LM Studio > Program tab (right sidebar) > Install > Edit mcp.json

**Configuration:**
```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "searchmcp"
    }
  }
}
```

LM Studio auto-reloads when you save mcp.json. Ensure `uv tool` bin directory is in your system PATH (uv prints this during install).

### AnythingLLM

**Config file location:**
- macOS: `~/Library/Application Support/anythingllm-desktop/storage/plugins/anythingllm_mcp_servers.json`
- Linux: `~/.config/anythingllm-desktop/storage/plugins/anythingllm_mcp_servers.json`
- Windows: `%APPDATA%\anythingllm-desktop\storage\plugins\anythingllm_mcp_servers.json`

The file is created automatically when you first visit the "Agent Skills" page in the UI.

**Configuration:**
```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "searchmcp"
    }
  }
}
```

**Important:** In AnythingLLM, you must prefix your prompts with `@agent` to use MCP tools. Example: `@agent search for privacy tools`

You can manage MCP servers via the Agent Skills page without restarting the app.

### Qwen Code

**Option 1: CLI command:**
```bash
qwen mcp add searchmcp searchmcp
```

**Option 2: Edit config file directly:**

**Config file location:**
- User config: `~/.qwen/settings.json`
- Project config: `.qwen/settings.json`

**Configuration:**
```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "searchmcp"
    }
  }
}
```

**Manage servers:**
- List servers: `qwen mcp list`
- Remove server: `qwen mcp remove searchmcp`

### Generic MCP Client

For other clients, configure an MCP server with:
- **Command:** `searchmcp`
- **Transport:** stdio

## Step 5: Verify Installation

1. **Restart the MCP client** (quit completely and reopen)

2. **Check Tor is running:**
```bash
# Should return a JSON with Tor exit IP
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip
```

3. **Test the search tool** by asking the MCP client to search for something

## Troubleshooting

### "Cannot connect to Tor proxy"
Tor service is not running. Start it:
- macOS: `brew services start tor`
- Linux: `sudo systemctl start tor`
- Windows: Run tor.exe

### "Command not found: searchmcp"
uv tool bin directory is not in PATH. Run:
```bash
uv tool update-shell
```
Then restart your terminal.

### MCP server not appearing
1. Verify JSON is valid (no trailing commas, proper quotes)
2. Restart the MCP client completely
3. Run `searchmcp --help` in a terminal to confirm the command works

### Slow searches
Normal - Tor adds latency for privacy. Searches may take 2-5 seconds longer than direct connections.

### LM Studio: MCP server not loading
1. Check JSON syntax in mcp.json (use the in-app editor)
2. Ensure `searchmcp` is in your system PATH
3. Try restarting LM Studio completely

### AnythingLLM: Tools not working
1. Make sure you prefix prompts with `@agent`
2. Check the Agent Skills page to verify the server started
3. Click "Refresh" on the Agent Skills page to reload servers

### Claude Code: Server not connecting
1. Run `/mcp` to check server status
2. Remove and re-add: `claude mcp remove searchmcp` then add again
3. Check `searchmcp --help` works in a terminal

### Qwen Code: Server not loading
1. Run `qwen mcp list` to verify server is configured
2. Check JSON syntax in settings.json
3. Ensure `searchmcp` is in your PATH

## Privacy Verification

Once working, the user should see this in their MCP client's logs or server output:
```
SEARCHMCP - Privacy Mode ENABLED
  [✓] Tor proxy: socks5h://127.0.0.1:9050
  [✓] Tor verified: exit IP xxx.xxx.xxx.xxx
  [✓] Query logging: DISABLED
```

If they see "Privacy Mode DISABLED", Tor is not configured correctly.
```

</details>

## License

Apache 2.0 License - See LICENSE file for details.

## Contributing

Contributions welcome! Please ensure all changes maintain privacy-by-default
behavior and include tests.

## Disclaimer

SearchMCP provides privacy through Tor routing, but no system is perfect.
For activities requiring the highest level of anonymity, consider using Tails OS
and additional operational security measures. This tool is for legitimate
privacy protection, not for illegal activities.
