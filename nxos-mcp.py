#!/usr/bin/env python3
"""
Cisco NX-OS CLI MCP Server

This MCP server enables sending arbitrary CLI commands to one or more Cisco NX-OS switches
via their NX-API interface. Commands are sent as text and responses default to text format.

Usage:
    See README file for installation instructions. 
    This code is meant to be integrated as a MCP server with Claude Desktop, Visual Studio Code or any other AI agent.
    
Required Environment Variables (set in .env file or passed as parameters):
    NXOS_USERNAME: Username for NX-OS device authentication
    NXOS_PASSWORD: Password for NX-OS device authentication
"""

import logging
import json
import os
from enum import Enum
from typing import Dict, List, Optional, Any
from base64 import b64encode

import httpx
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file and init logger
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logger = logging.getLogger("nxos_cli_mcp")

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
# Input Models - this code uses Pydantic for data validation
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
        min_length=1,
        max_length=MAX_COMMANDS
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
        min_length=1,
        max_length=MAX_DEVICES
    )
    commands: List[str] = Field(
        ...,
        description="List of CLI commands to execute on all devices (e.g., ['show version', 'show interface brief'])",
        min_length=1,
        max_length=MAX_COMMANDS
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

def is_config_command(commands: List[str]) -> bool:
    """
    Detect if commands contain configuration mode commands.
    Returns True if any command starts with 'conf' or 'configure'.
    """
    config_prefixes = ('conf t', 'conf', 'configure terminal', 'configure')
    for cmd in commands:
        cmd_lower = cmd.lower().strip()
        if any(cmd_lower.startswith(prefix) for prefix in config_prefixes):
            return True
    return False


def build_jsonrpc_payload(commands: List[str]) -> List[Dict[str, Any]]:
    """
    Build JSON-RPC payload for configuration commands.
    Each command becomes a separate JSON-RPC request with sequential IDs.
    """
    payload = []
    for i, cmd in enumerate(commands, start=1):
        payload.append({
            "jsonrpc": "2.0",
            "method": "cli",
            "params": {
                "cmd": cmd,
                "version": 1
            },
            "id": i
        })
    return payload


def parse_jsonrpc_response(
    response_data: List[Dict[str, Any]],
    commands: List[str]
) -> List[Dict[str, Any]]:
    """
    Parse JSON-RPC response format into standardized results.
    """
    results = []
    for i, resp in enumerate(response_data):
        cmd = commands[i] if i < len(commands) else "unknown"

        if "error" in resp:
            error_info = resp["error"]
            results.append({
                "command": cmd,
                "output": "",
                "error": error_info.get("message", str(error_info)),
                "code": error_info.get("code", "unknown")
            })
        else:
            # Extract result - can be string, dict, or None
            result = resp.get("result", "")
            if result is None:
                result = ""
            elif isinstance(result, dict):
                # Handle structured response (may contain 'msg' or 'body')
                if "msg" in result:
                    result = result["msg"]
                elif "body" in result:
                    body = result["body"]
                    if isinstance(body, dict):
                        result = json.dumps(body, indent=2)
                    else:
                        result = str(body) if body else ""
                else:
                    result = json.dumps(result, indent=2)
            elif not isinstance(result, str):
                result = str(result)

            results.append({
                "command": cmd,
                "output": result
            })

    return results


def get_credentials(username: Optional[str], password: Optional[str]) -> tuple[str, str]:
    """
    Get credentials from parameters or environment variables.
    """
    user = username or os.getenv("NXOS_USERNAME")
    pwd = password or os.getenv("NXOS_PASSWORD")

    logger.debug("Resolving credentials: username=%s, password=%s", 
                 "PROVIDED" if password else "FROM_ENV", 
                 "PROVIDED" if password else "FROM_ENV")

    if not user or not pwd:
        logger.error("Missing NX-OS credentials")
        raise ValueError(
            "Authentication credentials not provided. "
            "Set NXOS_USERNAME and NXOS_PASSWORD in .env file "
            "or provide username and password parameters in query."
        )

    return user, pwd

def create_auth_header(username: str, password: str) -> str:
    credentials = f"{username}:{password}"
    encoded = b64encode(credentials.encode()).decode()
    logger.debug("Generated Basic auth header for user %s", username)
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
    Automatically detects configuration commands and uses JSON-RPC format.
    """
    url = f"https://{ip_address}/ins"
    auth_header = create_auth_header(username, password)

    # Detect if this is a configuration command sequence
    use_jsonrpc = is_config_command(commands)

    if use_jsonrpc:
        # Use JSON-RPC format for configuration commands
        payload = build_jsonrpc_payload(commands)
        headers = {
            "Content-Type": "application/json-rpc",
            "Authorization": auth_header
        }
        logger.info("Sending %d config command(s) to device %s via JSON-RPC (timeout=%ss)",
                    len(commands), ip_address, timeout)
    else:
        # Use ins_api format for show commands
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
        logger.info("Sending %d show command(s) to device %s via ins_api (timeout=%ss)",
                    len(commands), ip_address, timeout)

    logger.debug("Request URL: %s", url)
    logger.debug("Request payload: %s", json.dumps(payload))

    try:
        async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            logger.debug("Received HTTP %s from %s", response.status_code, ip_address)
            response.raise_for_status()
            data = response.json()

        # Parse response based on format used
        if use_jsonrpc:
            # Parse JSON-RPC response format
            if not isinstance(data, list):
                data = [data]
            results = parse_jsonrpc_response(data, commands)
            logger.info("Config commands on %s completed successfully", ip_address)
            return {
                "success": True,
                "device": ip_address,
                "results": results
            }
        else:
            # Parse ins_api response format
            if "ins_api" in data and "outputs" in data["ins_api"]:
                outputs = data["ins_api"]["outputs"]["output"]
                if not isinstance(outputs, list):
                    outputs = [outputs]

                results = []
                for i, output in enumerate(outputs):
                    # Extract body and ensure it's a string
                    body = output.get("body", "")
                    if isinstance(body, dict):
                        body = json.dumps(body, indent=2)
                    elif not isinstance(body, str):
                        body = str(body)

                    result = {
                        "command": commands[i] if i < len(commands) else "unknown",
                        "output": body
                    }

                    # Include error info if present
                    if output.get("code") != "200":
                        result["error"] = output.get("msg", "Command failed")
                        result["code"] = output.get("code", "unknown")

                    results.append(result)

                logger.info("Show commands on %s completed successfully", ip_address)
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
        logger.error("HTTP error on %s: %s", ip_address, error_msg)
        return {
            "success": False,
            "device": ip_address,
            "error": error_msg
        }
    except httpx.TimeoutException:
        logger.error("Timeout after %ss for device %s", timeout, ip_address)
        return {
            "success": False,
            "device": ip_address,
            "error": f"Request timed out after {timeout} seconds"
        }
    except Exception as e:
        logger.exception("Unexpected error executing commands on %s", ip_address)
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

@mcp.tool()
async def nxos_execute_commands(params: SingleDeviceCommandInput) -> str:
    logger.info(
        "nxos_execute_commands called: ip=%s, commands=%s, format=%s, timeout=%s",
        params.ip_address,
        params.commands,
        params.response_format,
        params.timeout,
    )
    try:
        username, password = get_credentials(params.username, params.password)
        result = await execute_cli_command(
            ip_address=params.ip_address,
            commands=params.commands,
            username=username,
            password=password,
            timeout=params.timeout
        )
        logger.debug("Execution result: %s", result)
        if params.response_format == ResponseFormat.TEXT:
            output = format_text_response(result)
        else:
            output = json.dumps(result, indent=2)
        logger.info("nxos_execute_commands completed for %s", params.ip_address)
        return output

    except ValueError as e:
        logger.error("Validation error: %s", e)
        return f"Error: {e}"
    except Exception as e:
        logger.exception("Unexpected error in nxos_execute_commands")
        return f"Unexpected error: {type(e).__name__}: {e}"

@mcp.tool()
async def nxos_execute_commands_multi(params: MultiDeviceCommandInput) -> str:
    logger.info(
        "nxos_execute_commands_multi called: ips=%s, commands=%s, continue_on_error=%s, timeout=%s",
        params.ip_addresses,
        params.commands,
        params.continue_on_error,
        params.timeout,
    )
    try:
        username, password = get_credentials(params.username, params.password)
        results = []
        for ip in params.ip_addresses:
            res = await execute_cli_command(
                ip_address=ip,
                commands=params.commands,
                username=username,
                password=password,
                timeout=params.timeout
            )
            results.append(res)
            if not params.continue_on_error and not res["success"]:
                logger.warning("Stopping execution due to error on %s", ip)
                break

        logger.debug("Aggregated results: %s", results)
        if params.response_format == ResponseFormat.TEXT:
            output = format_multi_device_text_response(results)
        else:
            summary = {
                "total_devices": len(params.ip_addresses),
                "successful": sum(1 for r in results if r["success"]),
                "failed": sum(1 for r in results if not r["success"]),
                "results": results
            }
            output = json.dumps(summary, indent=2)
        logger.info("nxos_execute_commands_multi completed")
        return output

    except ValueError as e:
        logger.error("Validation error: %s", e)
        return f"Error: {e}"
    except Exception as e:
        logger.exception("Unexpected error in nxos_execute_commands_multi")
        return f"Unexpected error: {type(e).__name__}: {e}"

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting nxos_cli_mcp server")
    mcp.run()
