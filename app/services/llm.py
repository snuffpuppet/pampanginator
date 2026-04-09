"""
LLM service — reads config/llm.yaml and exposes a single complete() function.

Switching between Anthropic and any OpenAI-compatible backend (Ollama, etc.)
is a configuration change in config/llm.yaml, not a code change. The agentic
tool-call loop runs for both backends when tools_enabled is true.
"""

import json
import os
import time
import yaml
from pathlib import Path
import anthropic
import httpx
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from .tool_router import get_tool_definitions, dispatch
from metrics import LLM_TOKENS_TOTAL, LLM_CALL_DURATION

LLM_CONFIG_PATH = "/app/config/llm.yaml"
SYSTEM_PROMPT_PATH = "/app/config/system_prompt.md"

tracer = trace.get_tracer(__name__)

_backend: dict = {}
_client: anthropic.AsyncAnthropic | None = None
_system_prompt: str | None = None

# Set during init(); used by routes for metric labels.
ACTIVE_BACKEND: str = ""
ACTIVE_MODEL: str = ""


def init(
    llm_config_path: str = LLM_CONFIG_PATH,
    system_prompt_path: str = SYSTEM_PROMPT_PATH,
) -> None:
    """Read llm.yaml, select the active backend, initialise the API client."""
    global _backend, _client, _system_prompt, ACTIVE_BACKEND, ACTIVE_MODEL

    with open(llm_config_path) as f:
        config = yaml.safe_load(f)

    active = os.getenv("BACKEND", config.get("active_backend", "anthropic"))
    backends = config.get("backends", {})
    if active not in backends:
        raise ValueError(f"Backend '{active}' not found in {llm_config_path}")

    _backend = dict(backends[active])

    # Allow env var overrides for OpenAI-compatible backends (e.g. Ollama)
    if _backend.get("api_type") == "openai_compatible":
        if os.getenv("OLLAMA_URL"):
            _backend["base_url"] = os.environ["OLLAMA_URL"]
        if os.getenv("OLLAMA_MODEL"):
            _backend["model"] = os.environ["OLLAMA_MODEL"]

    if _backend.get("api_type") == "anthropic":
        _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    _system_prompt = Path(system_prompt_path).read_text(encoding="utf-8")
    ACTIVE_BACKEND = active
    ACTIVE_MODEL = _backend["model"]


async def complete(messages: list[dict], session_id: str = "") -> tuple[str, list[str]]:
    """
    Send messages to the configured LLM backend, handle any tool calls, and return:
      (response_text, list_of_tool_names_used)

    The agentic loop runs for both backends when tools_enabled is true in llm.yaml.
    """
    api_type = _backend["api_type"]
    tools_enabled = _backend.get("tools_enabled", False)

    if api_type == "anthropic":
        return await _complete_anthropic(messages, session_id, tools_enabled)
    else:
        return await _complete_openai_compatible(messages, session_id, tools_enabled)


async def _complete_anthropic(
    messages: list[dict], session_id: str, tools_enabled: bool
) -> tuple[str, list[str]]:
    model = _backend["model"]
    max_tokens = _backend.get("max_tokens", 1024)
    tool_defs = get_tool_definitions(format="anthropic") if tools_enabled else []
    tools_used: list[str] = []
    current_messages = list(messages)

    with tracer.start_as_current_span("llm.complete") as outer_span:
        outer_span.set_attribute("llm.backend", "anthropic")
        outer_span.set_attribute("kapampangan.session_id", session_id)
        try:
            while True:
                with tracer.start_as_current_span("llm.call") as llm_span:
                    llm_span.set_attribute("llm.model", model)
                    llm_span.set_attribute("llm.max_tokens", max_tokens)
                    t0 = time.time()
                    try:
                        response = await _client.messages.create(
                            model=model,
                            max_tokens=max_tokens,
                            system=_system_prompt,
                            tools=tool_defs,
                            messages=current_messages,
                        )
                    except Exception as e:
                        llm_span.set_status(StatusCode.ERROR, str(e))
                        llm_span.record_exception(e)
                        raise

                    duration = time.time() - t0
                    llm_span.set_attribute("llm.input_tokens", response.usage.input_tokens)
                    llm_span.set_attribute("llm.output_tokens", response.usage.output_tokens)
                    llm_span.set_attribute("llm.stop_reason", response.stop_reason)

                    ctx = llm_span.get_span_context()
                    exemplar = {"TraceID": trace.format_trace_id(ctx.trace_id)} if ctx.is_valid else None
                    LLM_CALL_DURATION.labels(model=model).observe(duration, exemplar=exemplar)
                    LLM_TOKENS_TOTAL.labels(direction="input", model=model).inc(
                        response.usage.input_tokens, exemplar=exemplar
                    )
                    LLM_TOKENS_TOTAL.labels(direction="output", model=model).inc(
                        response.usage.output_tokens, exemplar=exemplar
                    )

                if response.stop_reason == "end_turn":
                    text = "".join(b.text for b in response.content if hasattr(b, "text"))
                    outer_span.set_attribute("kapampangan.tools_used_count", len(tools_used))
                    return text, tools_used

                if response.stop_reason == "tool_use":
                    tool_calls = [b for b in response.content if b.type == "tool_use"]
                    outer_span.set_attribute("kapampangan.tools_requested", len(tool_calls))
                    tool_results = []
                    for block in tool_calls:
                        tools_used.append(block.name)
                        result = await dispatch(block.name, block.input, session_id=session_id)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })
                    current_messages = current_messages + [
                        {"role": "assistant", "content": response.content},
                        {"role": "user", "content": tool_results},
                    ]
                    continue

                # Unexpected stop reason — return whatever text we have
                text = "".join(b.text for b in response.content if hasattr(b, "text"))
                return text, tools_used

        except Exception as e:
            outer_span.set_status(StatusCode.ERROR, str(e))
            outer_span.record_exception(e)
            raise


async def _complete_openai_compatible(
    messages: list[dict], session_id: str, tools_enabled: bool
) -> tuple[str, list[str]]:
    model = _backend["model"]
    base_url = _backend["base_url"]
    max_tokens = _backend.get("max_tokens", 1024)
    tool_defs = get_tool_definitions(format="openai") if tools_enabled else []
    tools_used: list[str] = []
    current_messages = [{"role": "system", "content": _system_prompt}] + list(messages)

    with tracer.start_as_current_span("llm.complete") as outer_span:
        outer_span.set_attribute("llm.backend", "openai_compatible")
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
                                f"{base_url}/v1/chat/completions",
                                json=body,
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

                if finish_reason == "tool_calls":
                    tool_calls = message.get("tool_calls", [])
                    outer_span.set_attribute("kapampangan.tools_requested", len(tool_calls))
                    current_messages.append({
                        "role": "assistant",
                        "content": message.get("content"),
                        "tool_calls": tool_calls,
                    })
                    for tc in tool_calls:
                        tool_name = tc["function"]["name"]
                        tool_input = json.loads(tc["function"]["arguments"])
                        tools_used.append(tool_name)
                        result = await dispatch(tool_name, tool_input, session_id=session_id)
                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": str(result),
                        })
                    continue

                text = message.get("content") or ""
                outer_span.set_attribute("kapampangan.tools_used_count", len(tools_used))
                return text, tools_used

        except Exception as e:
            outer_span.set_status(StatusCode.ERROR, str(e))
            outer_span.record_exception(e)
            raise
