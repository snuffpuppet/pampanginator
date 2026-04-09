"""
Tool router — reads tools.yaml and dispatches tool calls to MCP servers.

At startup, load_tools() is called once. The loaded tool definitions are
passed to every LLM API call so the model can decide which tools to invoke.

When the model returns a tool call, dispatch() sends the parameters to the
appropriate MCP server and returns the result.
"""

import os
import yaml
import httpx
from pathlib import Path
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from metrics import TOOL_CALLS_TOTAL

tracer = trace.get_tracer(__name__)


_tools: list[dict] = []


def load_tools(config_path: str = "/app/config/tools.yaml") -> None:
    global _tools
    with open(config_path) as f:
        config = yaml.safe_load(f)

    _tools = []
    for tool in config.get("tools", []):
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
            "input_schema": {   # stored in Anthropic format; converted on demand by get_tool_definitions()
                "type": "object",
                "properties": properties,
                "required": required,
            },
            "_endpoint":        tool["endpoint"],
            "_method":          tool.get("method", "POST").upper(),
            "_timeout_seconds": float(tool.get("timeout_seconds", 10)),
        })


def get_tool_definitions(format: str = "anthropic") -> list[dict]:
    """Return tool definitions in the requested API format.

    format="anthropic" — Anthropic tool schema (input_schema key)
    format="openai"    — OpenAI function calling schema (parameters key,
                         wrapped in {type: function, function: {...}})
    """
    if format == "openai":
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
            for tool in _tools
        ]
    return [
        {k: v for k, v in tool.items() if not k.startswith("_")}
        for tool in _tools
    ]


async def dispatch(tool_name: str, parameters: dict, session_id: str = "") -> dict:
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

    with tracer.start_as_current_span("tool.route") as span:
        span.set_attribute("tool.name", tool_name)
        span.set_attribute("tool.endpoint", endpoint)
        span.set_attribute("kapampangan.session_id", session_id)
        TOOL_CALLS_TOTAL.labels(tool_name=tool_name).inc()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, endpoint, json=parameters)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            span.set_status(StatusCode.ERROR, f"{tool_name} returned {e.response.status_code}")
            return {"error": f"{tool_name} returned {e.response.status_code}", "detail": e.response.text}
        except httpx.RequestError as e:
            span.set_status(StatusCode.ERROR, f"{tool_name} unreachable")
            return {"error": f"{tool_name} unreachable", "detail": str(e)}
