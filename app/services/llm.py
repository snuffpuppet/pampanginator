"""
LLM service — reads config/llm.yaml and exposes a single complete() function.

Switching LLM backends or swapping models is a configuration change in
config/llm.yaml, not a code change. The agentic tool-call loop runs for any
backend when tools_enabled is true.

All backends use the OpenAI-compatible chat completions API. Set the
OPENROUTER_API_KEY environment variable to authenticate with OpenRouter.
The OPENROUTER_MODEL env var overrides the model declared in llm.yaml.
"""

import hashlib
import json
import logging
import os
import re
import time
import yaml
from pathlib import Path
import httpx
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from .tool_router import get_tool_definitions, dispatch
from metrics import LLM_TOKENS_TOTAL, LLM_CALL_DURATION

log = logging.getLogger(__name__)

LLM_CONFIG_PATH = "/app/config/llm.yaml"
SYSTEM_PROMPT_PATH = "/app/config/system_prompt.md"

tracer = trace.get_tracer(__name__)

_backend: dict = {}
_system_prompt: str | None = None

# Set during init(); used by routes for metric labels and interaction logging.
ACTIVE_BACKEND: str = ""
ACTIVE_MODEL: str = ""
ACTIVE_MODEL_B: str = ""  # comparison model for /api/chat/model-b
SYSTEM_PROMPT_VERSION: str = ""  # first 8 hex chars of SHA-256 of the system prompt


def init(
    llm_config_path: str = LLM_CONFIG_PATH,
    system_prompt_path: str = SYSTEM_PROMPT_PATH,
) -> None:
    """Read llm.yaml, select the active backend, apply env var overrides."""
    global _backend, _system_prompt, ACTIVE_BACKEND, ACTIVE_MODEL, ACTIVE_MODEL_B, SYSTEM_PROMPT_VERSION

    with open(llm_config_path) as f:
        config = yaml.safe_load(f)

    active = os.getenv("BACKEND", config.get("active_backend", "openrouter"))
    backends = config.get("backends", {})
    if active not in backends:
        raise ValueError(f"Backend '{active}' not found in {llm_config_path}")

    _backend = dict(backends[active])

    # Allow env var override for model selection
    if os.getenv("OPENROUTER_MODEL"):
        _backend["model"] = os.environ["OPENROUTER_MODEL"]

    _system_prompt = Path(system_prompt_path).read_text(encoding="utf-8")
    ACTIVE_BACKEND = active
    ACTIVE_MODEL = _backend["model"]
    ACTIVE_MODEL_B = _backend.get("model_b", ACTIVE_MODEL)
    SYSTEM_PROMPT_VERSION = hashlib.sha256(_system_prompt.encode()).hexdigest()[:8]


async def complete(messages: list[dict], session_id: str = "") -> tuple[str, list[str]]:
    """
    Send messages to the configured LLM backend, handle any tool calls, and return:
      (response_text, list_of_tool_names_used)

    The agentic loop runs when tools_enabled is true in llm.yaml.
    """
    tools_enabled = _backend.get("tools_enabled", False)
    return await _complete_openai_compatible(messages, session_id, tools_enabled)


async def complete_with_model(
    messages: list[dict], model: str, session_id: str = ""
) -> tuple[str, list[str]]:
    """Complete using an explicit model override (used by comparison endpoints)."""
    tools_enabled = _backend.get("tools_enabled", False)
    return await _complete_openai_compatible(messages, session_id, tools_enabled, model_override=model)


def _try_parse_text_tool_call(content: str) -> tuple[str, dict] | None:
    """
    Some smaller models (e.g. llama3.2) output tool calls as plain text content
    instead of using the tool_calls API mechanism, producing output like:
        {"name": grammar_lookup, "parameters": {"root": "..."}}
    Detect and parse these so the agentic loop can handle them correctly
    rather than leaking raw JSON to the user.
    Returns (tool_name, parameters) or None if content is not a tool call.
    """
    content = content.strip()
    if not content.startswith("{"):
        return None

    known_tools = {t["function"]["name"] for t in get_tool_definitions(format="openai")}

    data = None
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Fix unquoted identifier values (with or without spaces):
        #   `"name": grammar_lookup,`     → `"name": "grammar_lookup",`
        #   `"name": vocabulary Lookup,`  → `"name": "vocabulary Lookup",`
        fixed = re.sub(r":\s*([A-Za-z_][A-Za-z0-9_ ]*?)\s*([,}])", r': "\1"\2', content)
        # Fix spurious backslash before a closing quote in key names:
        #   `"term\"` → `"term"`
        fixed = re.sub(r'"([^"\\]*)\\"', r'"\1"', fixed)
        try:
            data = json.loads(fixed)
        except json.JSONDecodeError:
            return None

    if not isinstance(data, dict):
        return None

    name = data.get("name")
    if isinstance(name, str):
        # Normalise: some models use wrong case or spaces ("vocabulary Lookup" → "vocabulary_lookup")
        normalized = name.lower().replace(" ", "_")
        if normalized in known_tools:
            name = normalized

    params = data.get("parameters") or data.get("arguments") or {}
    if name in known_tools and isinstance(params, dict):
        return name, params
    return None


async def _complete_openai_compatible(
    messages: list[dict], session_id: str, tools_enabled: bool, model_override: str | None = None
) -> tuple[str, list[str]]:
    model = model_override or _backend["model"]
    base_url = _backend["base_url"]
    max_tokens = _backend.get("max_tokens", 1024)
    tool_defs = get_tool_definitions(format="openai") if tools_enabled else []
    tools_used: list[str] = []
    current_messages = [{"role": "system", "content": _system_prompt}] + list(messages)

    # Build auth header if an API key is configured
    headers: dict[str, str] = {}
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    with tracer.start_as_current_span("llm.complete") as outer_span:
        outer_span.set_attribute("llm.backend", ACTIVE_BACKEND)
        outer_span.set_attribute("llm.base_url", base_url)
        outer_span.set_attribute("kapampangan.session_id", session_id)
        try:
            while True:
                body: dict = {
                    "model": model,
                    "messages": current_messages,
                    "max_tokens": max_tokens,
                    "stream": False,
                }
                if tool_defs:
                    body["tools"] = tool_defs

                with tracer.start_as_current_span("llm.call") as llm_span:
                    llm_span.set_attribute("llm.model", model)
                    t0 = time.time()
                    try:
                        async with httpx.AsyncClient(timeout=120.0) as client:
                            resp = await client.post(
                                f"{base_url}/chat/completions",
                                json=body,
                                headers=headers,
                            )
                            resp.raise_for_status()
                            data = resp.json()
                    except Exception as e:
                        llm_span.set_status(StatusCode.ERROR, str(e))
                        llm_span.record_exception(e)
                        raise

                    duration = time.time() - t0
                    usage = data.get("usage", {})
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)
                    llm_span.set_attribute("llm.input_tokens", input_tokens)
                    llm_span.set_attribute("llm.output_tokens", output_tokens)

                    ctx = llm_span.get_span_context()
                    exemplar = {"TraceID": trace.format_trace_id(ctx.trace_id)} if ctx.is_valid else None
                    LLM_CALL_DURATION.labels(model=model).observe(duration, exemplar=exemplar)
                    if input_tokens:
                        LLM_TOKENS_TOTAL.labels(direction="input", model=model).inc(
                            input_tokens, exemplar=exemplar
                        )
                    if output_tokens:
                        LLM_TOKENS_TOTAL.labels(direction="output", model=model).inc(
                            output_tokens, exemplar=exemplar
                        )

                choice = data["choices"][0]
                finish_reason = choice.get("finish_reason")
                message = choice["message"]

                log.info(
                    "llm call complete",
                    extra={
                        "model": model,
                        "finish_reason": finish_reason,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "duration_s": round(duration, 3),
                        "session_id": session_id,
                    },
                )

                if finish_reason == "tool_calls":
                    tool_calls = message.get("tool_calls", [])
                    outer_span.set_attribute("kapampangan.tools_requested", len(tool_calls))
                    log.info("tool calls requested", extra={"tools": [tc["function"]["name"] for tc in tool_calls], "session_id": session_id})
                    current_messages.append({
                        "role": "assistant",
                        "content": message.get("content"),
                        "tool_calls": tool_calls,
                    })
                    for tc in tool_calls:
                        tool_name = tc["function"]["name"]
                        tool_input = json.loads(tc["function"]["arguments"])
                        result = await dispatch(tool_name, tool_input, session_id=session_id)
                        if "error" not in result:
                            tools_used.append(tool_name)
                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": str(result),
                        })
                    continue

                text = message.get("content") or ""

                # Detect text-based tool call: some models output the tool call
                # as plain text content instead of using the tool_calls API.
                if text:
                    parsed = _try_parse_text_tool_call(text)
                    if parsed is not None:
                        tool_name, tool_input = parsed
                        outer_span.set_attribute("kapampangan.tools_requested", 1)
                        result = await dispatch(tool_name, tool_input, session_id=session_id)
                        if "error" not in result:
                            tools_used.append(tool_name)
                        current_messages.append({"role": "assistant", "content": text})
                        current_messages.append({"role": "user", "content": str(result)})
                        continue

                outer_span.set_attribute("kapampangan.tools_used_count", len(tools_used))
                return text, tools_used

        except Exception as e:
            outer_span.set_status(StatusCode.ERROR, str(e))
            outer_span.record_exception(e)
            raise
