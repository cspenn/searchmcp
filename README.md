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
