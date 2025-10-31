## Kali Pentest MCP

Non-root Kali-based MCP server exposing safe wrappers for nmap, nikto, sqlmap, wpscan, dirb, and searchsploit. Inputs are sanitized, outputs are plain text, concurrency limited, and results are truncated to prevent overload.

### Tools
- nmap: service/version scan with safe defaults
- nikto: web checks
- sqlmap: basic SQLi test with safe defaults
- wpscan: WordPress scanning with optional API token
- dirb: directory brute-force with optional wordlist
- searchsploit: local Exploit-DB search

### Environment Variables
- ALLOWED_HOST_REGEX: regex to permit targets (default `.*`)
- SCAN_TIMEOUT_SECONDS: per-tool timeout seconds (default `600`)
- MAX_OUTPUT_KB: truncate output to this size (default `512`)
- WPSCAN_API_TOKEN: optional WPScan token
- HTTP_PROXY / HTTPS_PROXY: optional proxies
- DNS_SERVERS: comma-separated list for nmap `--dns-servers`

### Security Notes
- Runs as non-root user
- Requires container capabilities: NET_RAW, NET_BIND_SERVICE
- Sanitizes flags to a small allowlist per tool
- Blocks targets that do not match `ALLOWED_HOST_REGEX`

### Concurrency
- Max 2 concurrent tool runs

## Installation

1. Build the Docker image:
```powershell
docker build -t dice-mcp-server .
```

2. Run the container with required capabilities:
```powershell
docker run --rm -it `
  --name dice-mcp-server `
  --cap-add=NET_RAW `
  --cap-add=NET_BIND_SERVICE `
  -e ALLOWED_HOST_REGEX="^(10\.|192\.168\.|localhost|127\.0\.0\.1)" `
  -e SCAN_TIMEOUT_SECONDS="600" `
  -e MAX_OUTPUT_KB="512" `
  dice-mcp-server
```

## MCP Configuration

Add this to your MCP client configuration (example for Claude Desktop):

```json
{
  "mcpServers": {
    "dice-mcp-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--cap-add=NET_RAW",
        "--cap-add=NET_BIND_SERVICE",
        "-e", "ALLOWED_HOST_REGEX=^(10\\.|192\\.168\\.|localhost|127\\.0\\.0\\.1)",
        "-e", "SCAN_TIMEOUT_SECONDS=600",
        "-e", "MAX_OUTPUT_KB=512",
        "dice-mcp-server"
      ]
    }
  }
}
```

## Available Tools

### `nmap_scan`
Runs a safe nmap scan against a host or IP.
- **target**: Host or IP address (required)
- **flags**: Optional nmap flags (e.g., "-F", "-p 80,443")

### `nikto_scan`
Runs nikto web server checks against a URL.
- **url**: Target URL (required)
- **flags**: Optional nikto flags

### `sqlmap_test`
Runs a basic sqlmap test against a URL with safe defaults.
- **url**: Target URL with parameter (required)
- **flags**: Optional sqlmap flags

### `wpscan_site`
Runs WPScan against a WordPress target URL.
- **url**: WordPress site URL (required)
- **flags**: Optional wpscan flags (e.g., "--enumerate u")

### `dirb_scan`
Runs dirb against a URL with an optional wordlist.
- **url**: Target URL (required)
- **wordlist**: Optional wordlist name (e.g., "dirb/common.txt")

### `searchsploit_query`
Searches local Exploit-DB with searchsploit.
- **query**: Search query (required)
- **flags**: Optional searchsploit flags

## Example Usage

```
nmap_scan(target="192.168.1.10", flags="-F")
nikto_scan(url="http://192.168.1.10")
sqlmap_test(url="http://192.168.1.10/page.php?id=1")
wpscan_site(url="http://192.168.1.20", flags="--enumerate u")
dirb_scan(url="http://192.168.1.10", wordlist="dirb/common.txt")
searchsploit_query(query="apache 2.4.49")
```

