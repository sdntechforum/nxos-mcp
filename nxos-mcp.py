#!/usr/bin/env python3
"""
Cisco NX-OS CLI MCP Server

This MCP server enables sending arbitrary CLI commands to one or more Cisco NX-OS switches
via their NX-API interface. Commands are sent as text and responses default to text format.

Usage:
    uv run nxos_cli_mcp.py

Required Environment Variables (set in .env file):
    NXOS_USERNAME: Username for NX-OS device authentication
    NXOS_PASSWORD: Password for NX-OS device authentication

Example .env file:
    NXOS_USERNAME=admin
    NXOS_PASSWORD=your_password
"""

import json
import os
from enum import Enum
from typing import Dict, List, Optional, Any
from base64 import b64encode

import httpx
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("nxos_cli_mcp")

# Constants
DEFAULT_TIMEOUT = 30.0
MAX_DEVICES = 50
MAX_COMMANDS = 100


class ResponseFormat(str, Enum):
    """Response format for tool output."""
    TEXT = "text"
    JSON = "json"


# ============================================================================
# Input Models
# ============================================================================

class SingleDeviceCommandInput(BaseModel):
    """Input model for executing CLI commands on a single NX-OS device."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    ip_address: str = Field(
        ...,
        description="IP address or hostname of the NX-OS device (e.g., '192.168.1.1', '10.0.0.5')",
        min_length=7,
        max_length=253
    )
    commands: List[str] = Field(
        ...,
        description="List of CLI commands to execute (e.g., ['show version', 'show interface brief'])",
        min_items=1,
        max_items=MAX_COMMANDS
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.TEXT,
        description="Response format: 'text' (default, human-readable) or 'json' (structured data)"
    )
    username: Optional[str] = Field(
        default=None,
        description="Username for device authentication (overrides NXOS_USERNAME environment variable)"
    )
    password: Optional[str] = Field(
        default=None,
        description="Password for device authentication (overrides NXOS_PASSWORD environment variable)"
    )
    timeout: float = Field(
        default=DEFAULT_TIMEOUT,
        description="Request timeout in seconds",
        ge=1.0,
        le=300.0
    )

    @field_validator('commands')
    @classmethod
    def validate_commands(cls, v: List[str]) -> List[str]:
        """Validate that all commands are non-empty strings."""
        if not v:
            raise ValueError("At least one command must be provided")
        for cmd in v:
            if not cmd.strip():
                raise ValueError("Commands cannot be empty strings")
        return [cmd.strip() for cmd in v]

    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        """Validate IP address format."""
        v = v.strip()
        if not v:
            raise ValueError("IP address cannot be empty")
        return v


class MultiDeviceCommandInput(BaseModel):
    """Input model for executing CLI commands on multiple NX-OS devices."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    ip_addresses: List[str] = Field(
        ...,
        description="List of IP addresses or hostnames of NX-OS devices (e.g., ['192.168.1.1', '10.0.0.5'])",
        min_items=1,
        max_items=MAX_DEVICES
    )
    commands: List[str] = Field(
        ...,
        description="List of CLI commands to execute on all devices (e.g., ['show version', 'show interface brief'])",
        min_items=1,
        max_items=MAX_COMMANDS
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.TEXT,
        description="Response format: 'text' (default, human-readable) or 'json' (structured data)"
    )
    username: Optional[str] = Field(
        default=None,
        description="Username for device authentication (overrides NXOS_USERNAME environment variable)"
    )
    password: Optional[str] = Field(
        default=None,
        description="Password for device authentication (overrides NXOS_PASSWORD environment variable)"
    )
    timeout: float = Field(
        default=DEFAULT_TIMEOUT,
        description="Request timeout in seconds",
        ge=1.0,
        le=300.0
    )
    continue_on_error: bool = Field(
        default=True,
        description="Continue executing on other devices if one fails"
    )

    @field_validator('commands')
    @classmethod
    def validate_commands(cls, v: List[str]) -> List[str]:
        """Validate that all commands are non-empty strings."""
        if not v:
            raise ValueError("At least one command must be provided")
        for cmd in v:
            if not cmd.strip():
                raise ValueError("Commands cannot be empty strings")
        return [cmd.strip() for cmd in v]

    @field_validator('ip_addresses')
    @classmethod
    def validate_ip_addresses(cls, v: List[str]) -> List[str]:
        """Validate IP addresses are non-empty."""
        if not v:
            raise ValueError("At least one IP address must be provided")
        validated = []
        for ip in v:
            ip = ip.strip()
            if not ip:
                raise ValueError("IP addresses cannot be empty strings")
            validated.append(ip)
        return validated


# ============================================================================
# Helper Functions
# ============================================================================

def get_credentials(username: Optional[str], password: Optional[str]) -> tuple[str, str]:
    """
    Get credentials from parameters or environment variables.
    
    Args:
        username: Optional username parameter
        password: Optional password parameter
        
    Returns:
        Tuple of (username, password)
        
    Raises:
        ValueError: If credentials are not provided
    """
    user = username or os.getenv("NXOS_USERNAME")
    pwd = password or os.getenv("NXOS_PASSWORD")
    
    if not user or not pwd:
        raise ValueError(
            "Authentication credentials not provided. "
            "Set NXOS_USERNAME and NXOS_PASSWORD in .env file "
            "or provide username and password parameters."
        )
    
    return user, pwd


def create_auth_header(username: str, password: str) -> str:
    """
    Create Basic Authentication header value.
    
    Args:
        username: Username for authentication
        password: Password for authentication
        
    Returns:
        Base64-encoded Basic Auth header value
    """
    credentials = f"{username}:{password}"
    encoded = b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


async def execute_cli_command(
    ip_address: str,
    commands: List[str],
    username: str,
    password: str,
    timeout: float
) -> Dict[str, Any]:
    """
    Execute CLI commands on a single NX-OS device via NX-API.
    
    Args:
        ip_address: IP address or hostname of the device
        commands: List of CLI commands to execute
        username: Username for authentication
        password: Password for authentication
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary containing execution results
    """
    url = f"https://{ip_address}/ins"
    auth_header = create_auth_header(username, password)
    
    # Build NX-API payload - always use cli_show_ascii for text output
    payload = {
        "ins_api": {
            "version": "1.0",
            "type": "cli_show_ascii",
            "chunk": "0",
            "sid": "1",
            "input": " ;".join(commands),
            "output_format": "text"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": auth_header
    }
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response
            if "ins_api" in data and "outputs" in data["ins_api"]:
                outputs = data["ins_api"]["outputs"]["output"]
                if not isinstance(outputs, list):
                    outputs = [outputs]
                
                results = []
                for i, output in enumerate(outputs):
                    result = {
                        "command": commands[i] if i < len(commands) else "unknown",
                        "output": output.get("body", "")
                    }
                    
                    # Include error info if present
                    if output.get("code") != "200":
                        result["error"] = output.get("msg", "Command failed")
                        result["code"] = output.get("code", "unknown")
                    
                    results.append(result)
                
                return {
                    "success": True,
                    "device": ip_address,
                    "results": results
                }
            else:
                return {
                    "success": False,
                    "device": ip_address,
                    "error": f"Unexpected response format: {data}"
                }
                
    except httpx.HTTPStatusError as e:
        error_msg = format_http_error(e)
        return {
            "success": False,
            "device": ip_address,
            "error": error_msg
        }
    except httpx.TimeoutException:
        return {
            "success": False,
            "device": ip_address,
            "error": f"Request timed out after {timeout} seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "device": ip_address,
            "error": f"Unexpected error: {type(e).__name__}: {str(e)}"
        }


def format_http_error(error: httpx.HTTPStatusError) -> str:
    """Format HTTP error with helpful context."""
    status = error.response.status_code
    
    if status == 401:
        return "Authentication failed. Check username and password in .env file."
    elif status == 403:
        return "Permission denied. User may not have sufficient privileges."
    elif status == 404:
        return "NX-API endpoint not found. Verify the device supports NX-API."
    elif status == 500:
        return "Internal server error on device. Check command syntax or device status."
    else:
        return f"HTTP {status} error: {error.response.text[:200]}"


def format_text_response(result: Dict[str, Any]) -> str:
    """Format command results as plain text."""
    lines = [f"Device: {result['device']}", "=" * 80]
    
    if not result["success"]:
        lines.append(f"ERROR: {result['error']}")
        return "\n".join(lines)
    
    lines.append("Status: Success")
    lines.append("")
    
    for cmd_result in result["results"]:
        lines.append(f"Command: {cmd_result['command']}")
        lines.append("-" * 80)
        
        if "error" in cmd_result:
            lines.append(f"ERROR ({cmd_result.get('code', 'unknown')}): {cmd_result['error']}")
        else:
            lines.append(cmd_result["output"])
        
        lines.append("")
    
    return "\n".join(lines)


def format_multi_device_text_response(results: List[Dict[str, Any]]) -> str:
    """Format multi-device command results as plain text."""
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    lines = [
        "Multi-Device Command Execution",
        "=" * 80,
        f"Summary: {success_count}/{total_count} devices succeeded",
        "",
        ""
    ]
    
    for result in results:
        lines.append(format_text_response(result))
        lines.append("")
    
    return "\n".join(lines)


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool(
    name="nxos_execute_commands",
    annotations={
        "title": "Execute CLI Commands on Single NX-OS Device",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def nxos_execute_commands(params: SingleDeviceCommandInput) -> str:
    """Execute one or more CLI commands on a single Cisco NX-OS device via NX-API.
    
    This tool sends CLI commands to a Cisco NX-OS switch using the NX-API interface
    over HTTPS. It supports both read-only (show commands) and configuration commands.
    The device must have NX-API enabled (feature nxapi).
    
    Commands are always sent as text (cli_show_ascii) to NX-OS, and responses are
    returned as text by default (same as CLI output) or as JSON for structured parsing.
    
    Authentication credentials are obtained from either:
    1. The username/password parameters (highest priority)
    2. NXOS_USERNAME and NXOS_PASSWORD from .env file
    
    Args:
        params (SingleDeviceCommandInput): Input parameters containing:
            - ip_address (str): IP address or hostname of the NX-OS device
            - commands (List[str]): List of CLI commands to execute
            - response_format (ResponseFormat): Response format (text or json, default: text)
            - username (Optional[str]): Username for authentication
            - password (Optional[str]): Password for authentication
            - timeout (float): Request timeout in seconds (default: 30.0)
    
    Returns:
        str: Command execution results formatted as text or JSON
            
    Examples:
        Show commands:
        - commands: ["show version", "show interface brief"]
        
        Configuration commands:
        - commands: ["configure terminal", "interface Ethernet1/1", "description Test Port", "end"]
    """
    try:
        # Get credentials
        username, password = get_credentials(params.username, params.password)
        
        # Execute commands
        result = await execute_cli_command(
            ip_address=params.ip_address,
            commands=params.commands,
            username=username,
            password=password,
            timeout=params.timeout
        )
        
        # Format response
        if params.response_format == ResponseFormat.TEXT:
            return format_text_response(result)
        else:
            return json.dumps(result, indent=2)
            
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {str(e)}"


@mcp.tool(
    name="nxos_execute_commands_multi",
    annotations={
        "title": "Execute CLI Commands on Multiple NX-OS Devices",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def nxos_execute_commands_multi(params: MultiDeviceCommandInput) -> str:
    """Execute the same CLI command(s) on multiple Cisco NX-OS devices via NX-API.
    
    This tool sends identical CLI commands to multiple Cisco NX-OS switches concurrently
    using the NX-API interface over HTTPS. It's useful for gathering information or
    making configuration changes across multiple devices simultaneously.
    
    All devices must have NX-API enabled (feature nxapi) and be accessible via HTTPS.
    By default, execution continues even if some devices fail (continue_on_error=true).
    
    Commands are always sent as text (cli_show_ascii) to NX-OS, and responses are
    returned as text by default (same as CLI output) or as JSON for structured parsing.
    
    Authentication credentials are obtained from either:
    1. The username/password parameters (highest priority)
    2. NXOS_USERNAME and NXOS_PASSWORD from .env file
    
    Args:
        params (MultiDeviceCommandInput): Input parameters containing:
            - ip_addresses (List[str]): List of device IP addresses or hostnames
            - commands (List[str]): List of CLI commands to execute on all devices
            - response_format (ResponseFormat): Response format (text or json, default: text)
            - username (Optional[str]): Username for authentication
            - password (Optional[str]): Password for authentication
            - timeout (float): Request timeout in seconds per device (default: 30.0)
            - continue_on_error (bool): Continue if a device fails (default: true)
    
    Returns:
        str: Execution results for all devices formatted as text or JSON
            
    Examples:
        Gather version info from multiple switches:
        - ip_addresses: ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
        - commands: ["show version"]
        
        Configuration change across multiple devices:
        - ip_addresses: ["192.168.1.10", "192.168.1.11"]
        - commands: ["configure terminal", "logging server 10.1.1.1", "end"]
    """
    try:
        # Get credentials
        username, password = get_credentials(params.username, params.password)
        
        # Execute commands on all devices concurrently
        results = []
        for ip_address in params.ip_addresses:
            result = await execute_cli_command(
                ip_address=ip_address,
                commands=params.commands,
                username=username,
                password=password,
                timeout=params.timeout
            )
            results.append(result)
            
            # Stop if continue_on_error is False and we hit an error
            if not params.continue_on_error and not result["success"]:
                break
        
        # Format response
        if params.response_format == ResponseFormat.TEXT:
            return format_multi_device_text_response(results)
        else:
            summary = {
                "total_devices": len(params.ip_addresses),
                "successful": sum(1 for r in results if r["success"]),
                "failed": sum(1 for r in results if not r["success"]),
                "results": results
            }
            return json.dumps(summary, indent=2)
            
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {str(e)}"


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Use stdio transport for local integration
    mcp.run()
