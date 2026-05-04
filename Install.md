
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
# One or more Nexus devices — comma-separated.
# These are used as the default targets when no ip_address is supplied at query time.
NXOS_HOSTS=10.0.0.1,10.0.0.2,10.0.0.3
NXOS_USERNAME=admin
NXOS_PASSWORD=your_password
NXOS_PORT=443
NXOS_TRANSPORT=https
```

> **Note:** `NXOS_HOST` (singular) is still accepted for single-device backward compatibility,
> but `NXOS_HOSTS` (plural, comma-separated) is the recommended format going forward.

### Multi-Device Behaviour

The server exposes two tools:

| Tool | Description |
|---|---|
| `nxos_execute_commands` | Runs commands on a **single** device |
| `nxos_execute_commands_multi` | Runs commands across **multiple** devices in parallel |

Both tools accept an optional `ip_address` / `ip_addresses` parameter at query time.
When that parameter is **omitted**, the server falls back to the device list in `NXOS_HOSTS`:

| Call | Device(s) used |
|---|---|
| Provide `ip_address=10.0.0.5` | Only `10.0.0.5` |
| Omit `ip_address` | First device in `NXOS_HOSTS` |
| Omit `ip_addresses` in multi tool | **All** devices in `NXOS_HOSTS` |
| Provide `ip_addresses=["10.0.0.1","10.0.0.2"]` | Only the two specified |

**Example — run `show version` across all devices in `.env` without specifying IPs:**
```
nxos_execute_commands_multi(commands=["show version"])
```

**Example — run on a specific subset:**
```
nxos_execute_commands_multi(
    ip_addresses=["10.0.0.1", "10.0.0.3"],
    commands=["show interface brief"]
)
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
* **"No default devices configured" warning at startup:** The server logs this when `NXOS_HOSTS` is empty or missing. Tools still work — just supply `ip_address` explicitly at query time, or set `NXOS_HOSTS` in `.env`.
* **Migrating from `NXOS_HOST` (singular):** Replace `NXOS_HOST=10.0.0.1` with `NXOS_HOSTS=10.0.0.1` (or add more IPs). The server reads `NXOS_HOST` as a fallback so existing `.env` files continue to work without changes.
* **Reload after `.env` changes:** After editing `.env`, reload the MCP server in Cursor: `Cmd+Shift+P` → **Developer: Reload Window**. The server process must restart to pick up new environment variables.

```
