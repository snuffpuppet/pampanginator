"""
Tool router — reads tools.yaml and dispatches tool calls to MCP servers.

At startup, load_tools() is called once. The loaded tool definitions are
passed to every Anthropic API call so Claude can decide which tools to invoke.

When Claude returns a tool_use block, dispatch() sends the parameters to the
appropriate MCP server and returns the result.
"""

import os
import yaml
import httpx
from pathlib import Path


_tools: list[dict] = []


def load_tools(config_path: str = "/app/config/tools.yaml") -> None:
    global _tools
    with open(config_path) as f:
        config = yaml.safe_load(f)

    _tools = []
    for tool in config.get("tools", []):
        # Convert to Anthropic tool definition format
        properties = {}
        required = []
        for param in tool.get("parameters", []):
            properties[param["name"]] = {
                "type": param["type"],
                "description": param.get("description", ""),
            }
            if param.get("required"):
                required.append(param["name"])

        _tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
            "_endpoint":        tool["endpoint"],
            "_method":          tool.get("method", "POST").upper(),
            "_timeout_seconds": float(tool.get("timeout_seconds", 10)),
        })


def get_tool_definitions() -> list[dict]:
    """Return tool definitions in Anthropic API format (no internal fields)."""
    return [
        {k: v for k, v in tool.items() if not k.startswith("_")}
        for tool in _tools
    ]


async def dispatch(tool_name: str, parameters: dict) -> dict:
    """Send a tool call to its MCP server and return the response body."""
    tool = next((t for t in _tools if t["name"] == tool_name), None)
    if tool is None:
        return {"error": f"Unknown tool: {tool_name}"}

    endpoint = tool["_endpoint"]
    method   = tool["_method"]
    timeout  = tool["_timeout_seconds"]

    # Allow endpoint override via environment (useful for local dev without Docker)
    env_key  = f"{tool_name.upper()}_ENDPOINT"
    endpoint = os.getenv(env_key, endpoint)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(method, endpoint, json=parameters)
        response.raise_for_status()
        return response.json()
