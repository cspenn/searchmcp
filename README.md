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
SEARCHMCP_TOR_PROXY=socks5h://127.0.0.1:9150 python server.py
```

### 2. VPN (Recommended)

For defense in depth, use a VPN alongside Tor:

- **Mullvad VPN**: No account needed, privacy-focused
- **ProtonVPN**: From the ProtonMail team
- **IVPN**: Strong privacy policy

Connect to VPN first, then start Tor. This hides Tor usage from your ISP.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/searchmcp.git
cd searchmcp

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

## Quick Start

1. **Start Tor** (see Prerequisites above)

2. **Run SearchMCP:**
   ```bash
   python server.py
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

| Flag | Description |
|------|-------------|
| `--disable-privacy` | Disable Tor routing (not recommended) |
| `--with-logging` | Enable query content in logs for debugging |

**Examples:**
```bash
# Default: Maximum privacy
python server.py

# Debugging with query logging (use cautiously)
python server.py --with-logging

# Disable privacy mode (not recommended)
python server.py --disable-privacy
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
SEARCHMCP_TOR_PROXY=socks5h://127.0.0.1:9150 python server.py

# Increase timeout for slow connections
SEARCHMCP_TOR_TIMEOUT=60 python server.py
```

## MCP Client Configuration

Add to your MCP client configuration (e.g., Claude Desktop):

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
- Increase timeout: `SEARCHMCP_TOR_TIMEOUT=60 python server.py`
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

SearchMCP exposes three MCP tools:

### `web_search`
```python
web_search(
    query: str,           # Search query (required)
    max_results: int = 10,  # 1-100 results
    region: str = "wt-wt",  # Region code
    safe_search: str = "moderate"  # off/moderate/strict
) -> list[dict]
```

### `image_search`
```python
image_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt",
    safe_search: str = "moderate"
) -> list[dict]
```

### `news_search`
```python
news_search(
    query: str,
    max_results: int = 10,
    region: str = "wt-wt"
) -> list[dict]
```

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
3. **Python**: Do you have Python 3.10+ installed? (Check with `python3 --version`)
4. **uv**: Do you have uv installed? (Check with `uv --version`)
5. **Tor**: Do you have Tor installed? (Check with `tor --version`)

## Step 2: Install Prerequisites

Based on their OS, provide the appropriate commands:

### Python & uv

**macOS:**
```bash
# Install uv (includes Python management)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Linux (Debian/Ubuntu):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Linux (Fedora/RHEL):**
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
git clone https://github.com/cpsenn/searchmcp.git
cd searchmcp

# Install dependencies
uv sync
```

Ask the user for the FULL PATH to the searchmcp directory. They can find it with:
- macOS/Linux: `pwd` (while in the searchmcp directory)
- Windows: `cd` (while in the searchmcp directory)

## Step 4: Configure MCP Client

Based on their MCP client, provide the configuration:

### Claude Desktop

**Config file location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration (replace /path/to/searchmcp with actual path):**
```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/searchmcp", "python", "server.py"]
    }
  }
}
```

If they already have other MCP servers configured, help them merge the configuration.

### Claude Code (CLI)

**Option 1: CLI command (recommended):**
```bash
claude mcp add --transport stdio --scope user searchmcp -- uv run --directory /path/to/searchmcp python server.py
```

**Option 2: Edit config file directly:**

Config file: `~/.claude.json`

```json
{
  "mcpServers": {
    "searchmcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/searchmcp", "python", "server.py"]
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
      "command": "uv",
      "args": ["run", "--directory", "/path/to/searchmcp", "python", "server.py"]
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
          "command": "uv",
          "args": ["run", "--directory", "/path/to/searchmcp", "python", "server.py"]
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
      "command": "uv",
      "args": ["run", "--directory", "/path/to/searchmcp", "python", "server.py"]
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
      "command": "uv",
      "args": ["run", "--directory", "/path/to/searchmcp", "python", "server.py"]
    }
  }
}
```

LM Studio auto-reloads when you save mcp.json. Ensure `uv` is in your system PATH.

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
      "command": "uv",
      "args": ["run", "--directory", "/path/to/searchmcp", "python", "server.py"]
    }
  }
}
```

**Important:** In AnythingLLM, you must prefix your prompts with `@agent` to use MCP tools. Example: `@agent search for privacy tools`

You can manage MCP servers via the Agent Skills page without restarting the app.

### Qwen Code

**Option 1: CLI command:**
```bash
qwen mcp add searchmcp uv run --directory /path/to/searchmcp python server.py
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
      "command": "uv",
      "args": ["run", "--directory", "/path/to/searchmcp", "python", "server.py"]
    }
  }
}
```

**Manage servers:**
- List servers: `qwen mcp list`
- Remove server: `qwen mcp remove searchmcp`

### Generic MCP Client

For other clients, they need to configure an MCP server with:
- **Command:** `uv`
- **Arguments:** `["run", "--directory", "/path/to/searchmcp", "python", "server.py"]`
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

### "Command not found: uv"
Restart your terminal after installing uv, or run:
```bash
source ~/.bashrc  # or ~/.zshrc for zsh
```

### MCP server not appearing
1. Verify the path in the config is correct
2. Ensure the JSON is valid (no trailing commas, proper quotes)
3. Restart the MCP client completely

### Slow searches
Normal - Tor adds latency for privacy. Searches may take 2-5 seconds longer than direct connections.

### LM Studio: MCP server not loading
1. Check JSON syntax in mcp.json (use the in-app editor)
2. Ensure `uv` is in your system PATH
3. Try restarting LM Studio completely

### AnythingLLM: Tools not working
1. Make sure you prefix prompts with `@agent`
2. Check the Agent Skills page to verify the server started
3. Click "Refresh" on the Agent Skills page to reload servers

### Claude Code: Server not connecting
1. Run `/mcp` to check server status
2. Verify the path is correct: `claude mcp get searchmcp`
3. Remove and re-add: `claude mcp remove searchmcp` then add again
4. Check that `uv` is in your PATH

### Qwen Code: Server not loading
1. Run `qwen mcp list` to verify server is configured
2. Check JSON syntax in settings.json
3. Ensure `uv` is in your system PATH

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

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please ensure all changes maintain privacy-by-default
behavior and include tests.

## Disclaimer

SearchMCP provides privacy through Tor routing, but no system is perfect.
For activities requiring the highest level of anonymity, consider using Tails OS
and additional operational security measures. This tool is for legitimate
privacy protection, not for illegal activities.
