
## 📝 Part 1: `INSTALL.md`

```markdown
# Installing Cisco NX-OS MCP Server (macOS)

This guide documents the step-by-step process to install and connect the Cisco NX-OS MCP server to Cursor or any MCP-compliant client.

## 1. Prerequisites
- **Python 3.10+**
- **uv** (High-performance Python manager)
  ```bash
  curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

```

## 2. Installation

1. **Clone the repository:**
```bash
git clone https://github.com/sdntechforum/nxos-mcp.git nxos
cd nxos

```


2. **Initialize and Install Dependencies:**
*Pitfall: The repo may be missing the core MCP library.*
```bash
uv sync
uv add mcp  # Ensures the FastMCP framework is present

```



## 3. Configuration

Create a `.env` file in the root directory:

```bash
NXOS_HOST=YOUR_SWITCH_IP
NXOS_USERNAME=admin
NXOS_PASSWORD=your_password
NXOS_PORT=443
NXOS_TRANSPORT=https

```

## 4. Cursor Integration

Add the following to your `mcp.json` (found in Cursor Settings > Models > MCP):

```json
{
  "mcpServers": {
    "nxos": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/YOUR_USER/MCP/nxos",
        "run",
        "nxos-mcp.py"
      ]
    }
  }
}

```

## 5. Troubleshooting / Pitfalls

* **ModuleNotFoundError ('mcp'):** Run `uv add mcp`. The environment needs the specific MCP library to bridge with Cursor.
* **File Not Found (os error 2):** Double-check the filename. In this repo, it is `nxos-mcp.py` (hyphen), not `nxos_mcp.py` (underscore).
* **Process Hangs:** If running `uv run nxos-mcp.py` manually, it should show "Starting server" and then wait. This is normal behavior for stdio servers.

```
