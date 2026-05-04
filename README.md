# Cisco NX-OS CLI MCP Server

A Model Context Protocol (MCP) server that lets you interact with Cisco NX-OS devices. You can send arbitrary CLI commands to one or more switches via their NX-API interface. 
This server exposes MCP tools for executing commands on one or more devices with comprehensive error handling. The output format can also be selected (text or JSON).

## Features

- **Single Device Commands**: Execute CLI commands on individual NX-OS switches
- **Multi-Device Commands**: Execute the same commands across multiple switches concurrently
- **Text-Based I/O**: Commands are sent as text (cli_show_ascii), responses default to text format
- **JSON Option**: Optional JSON response format for structured parsing
- **Simple Authentication**: Credentials collected from .env file or on a per-request override
- **Error Handling**: Clear, actionable error messages
- **Batch Operations**: Execute up to 100 commands per request
- **Concurrent Execution**: Parallel command execution on multiple devices (up to 50)

## Requirements

- Python 3.10 or higher
- Cisco NX-OS devices with NX-API enabled (`feature nxapi`)
- Network connectivity between the MCP host (Claude Desktop, etc.) to target devices via HTTPS

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer (recommended)
- Cisco NX-OS devices with NX-API enabled (`feature nxapi`)
- Network connectivity to target devices via HTTPS

### Setup

1. Install uv (if not already installed):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. Install dependencies using uv:

```bash
# With uv and pyproject.toml (recommended)
uv sync
```

3. Set up authentication credentials:

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
NXOS_USERNAME=admin
NXOS_PASSWORD=your_secure_password
```

**Important**: Never commit your production `.env` file to version control. `.gitignore` is configured to prevent this but be cautious!

### Registering with MCP Hosts

#### Claude Desktop

**macOS:**

Edit the Claude Desktop configuration file:
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add the NX-OS CLI MCP server to the `mcpServers` section:
```json
{
  "mcpServers": {
    "nxos-cli": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/nxos-cli-mcp",
        "run",
        "nxos_cli_mcp.py"
      ]
    }
  }
}
```

**Windows:**

Edit the Claude Desktop configuration file:
```powershell
notepad %APPDATA%\Claude\claude_desktop_config.json
```

Add the NX-OS CLI MCP server to the `mcpServers` section:
```json
{
  "mcpServers": {
    "nxos-cli": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\absolute\\path\\to\\nxos-cli-mcp",
        "run",
        "nxos_cli_mcp.py"
      ]
    }
  }
}
```

After saving, restart Claude Desktop for the changes to take effect.

#### Visual Studio Code

**macOS:**

Edit the VS Code MCP settings file:
```bash
code ~/Library/Application\ Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
```

Add the server configuration:
```json
{
  "mcpServers": {
    "nxos-cli": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/nxos-cli-mcp",
        "run",
        "nxos_cli_mcp.py"
      ]
    }
  }
}
```

**Windows:**

Edit the VS Code MCP settings file:
```powershell
notepad %APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json
```

Add the server configuration:
```json
{
  "mcpServers": {
    "nxos-cli": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\absolute\\path\\to\\nxos-cli-mcp",
        "run",
        "nxos_cli_mcp.py"
      ]
    }
  }
}
```

After saving, reload the VS Code window (Command/Ctrl + Shift + P → "Developer: Reload Window").

**Important Notes:**
- Replace `/absolute/path/to/nxos-cli-mcp` (or `C:\absolute\path\to\nxos-cli-mcp`) with the actual full path to your project directory
- Ensure the `.env` file with your credentials is in the project directory
- The server will automatically load credentials from the `.env` file when started by the MCP client

### Available Tools

#### 1. nxos_execute_commands

Execute CLI commands on a single NX-OS device.

**Parameters:**
- `ip_address` (required): IP address or hostname of the device
- `commands` (required): List of CLI commands to execute
- `response_format` (optional): "text" (default, human-readable) or "json" (structured data)
- `username` (optional): Username for authentication
- `password` (optional): Password for authentication
- `timeout` (optional): Request timeout in seconds (default: 30)

#### 2. nxos_execute_commands_multi

Execute the same CLI commands on multiple NX-OS devices concurrently.

**Parameters:**
- `ip_addresses` (required): List of device IP addresses or hostnames (max 50)
- `commands` (required): List of CLI commands to execute on all devices
- `response_format` (optional): "text" (default, human-readable) or "json" (structured data)
- `username` (optional): Username for authentication
- `password` (optional): Password for authentication
- `timeout` (optional): Request timeout in seconds per device (default: 30)
- `continue_on_error` (optional): Continue executing on other devices if one fails (default: true)

## NX-API Configuration

Before using this MCP server, ensure NX-API is enabled on your NX-OS devices:

```
configure terminal
feature nxapi
nxapi http port 80
nxapi https port 443
```

Verify NX-API is running:
```
show nxapi
```

## Security Considerations

1. **Credentials**: Store credentials in the `.env` file, never commit the file to version control
2. **File Permissions**: Ensure `.env` has restricted permissions (`chmod 600 .env` on Unix systems)
3. **HTTPS**: This MCP server talks HTTPS to NX-API (with verification disabled for self-signed certificates; change this for production!)

## Output Formats

### How Commands Are Sent

All commands are sent to NX-OS devices as **text** using the `cli_show_ascii` API type. This ensures consistent behavior with the CLI experience you're familiar with.

### Response Formats

- **text** (default): Plain text output, identical to what you see in a CLI session
  - Easy to read in Claude Desktop or VS Code
  - Preserves formatting from the device
  - Best for interactive use

- **json**: Structured JSON response with detailed metadata, possibly better for MCP Hosts (experiment)
  - Includes success/failure status per device
  - Command execution results
  - Error details when applicable
  - Useful for programmatic parsing or complex workflows

## Error Handling

The server provides detailed error messages for common scenarios:

- **Authentication Failures**: "Authentication failed. Check username and password."
- **Permission Denied**: "Permission denied. User may not have sufficient privileges."
- **NX-API Not Found**: "NX-API endpoint not found. Verify the device supports NX-API."
- **Timeouts**: "Request timed out after X seconds"
- **Command Errors**: Includes command-specific error codes and messages from NX-OS

## Limitations

- Maximum 50 devices per multi-device command execution
- Maximum 100 commands per request
- Timeout range: 1-300 seconds
- SSL certificate verification is disabled (assumes self-signed certificates), change this in production!

## Troubleshooting

### Connection Refused
- Verify NX-API is enabled on the device: `show nxapi`
- Check network connectivity: `ping <device-ip>`
- Verify HTTPS port is accessible (default: 443)

### Authentication Failed
- Verify credentials in `.env` file are correct
- Check `.env` file exists in the project root directory
- Ensure `.env` file has proper format (no spaces around `=`)
- Verify the user account exists on the device
- Test credentials by SSH'ing to the device

### Command Execution Errors
- Verify command syntax is correct for NX-OS
- Check user has sufficient privileges for the command
- Review NX-OS command output for specific error details

### Timeout Issues
- Increase the timeout parameter for slow commands
- Check network latency to devices
- Consider splitting large command batches

### Testing

#### Run with MCP Inspector
```bash
npx @modelcontextprotocol/inspector uv run nxos_cli_mcp.py
```

## License

This MCP server is provided as-is under the MIT license.

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing patterns and conventions
- All functions have comprehensive docstrings
- Input validation is handled by Pydantic models
- Error messages are clear and actionable

## Support

For issues related to:
- **NX-API**: Consult Cisco NX-OS documentation
- **MCP Protocol**: Visit https://modelcontextprotocol.io
- **This Server**: Review error messages and troubleshooting section

[![MCP Badge](https://lobehub.com/badge/mcp/sdntechforum-nxos-mcp)](https://lobehub.com/mcp/sdntechforum-nxos-mcp)
