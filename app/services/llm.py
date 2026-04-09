"""
Anthropic API call assembly and execution.

Each call is stateless from the LLM's perspective. This service:
  1. Loads the system prompt from config/system_prompt.md
  2. Receives the conversation history from history.py
  3. Appends tool results when Claude has made tool calls
  4. Returns the final text response and a list of tool names used
"""

import os
import time
from pathlib import Path
import anthropic
import httpx
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from .tool_router import get_tool_definitions, dispatch
from metrics import LLM_TOKENS_TOTAL, LLM_CALL_DURATION

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024
SYSTEM_PROMPT_PATH = "/app/config/system_prompt.md"

BACKEND = os.getenv("BACKEND", "anthropic")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

_client: anthropic.AsyncAnthropic | None = None
_system_prompt: str | None = None

tracer = trace.get_tracer(__name__)


def init(system_prompt_path: str = SYSTEM_PROMPT_PATH) -> None:
    """Initialise the Anthropic client and load the system prompt. Call once at startup."""
    global _client, _system_prompt
    if BACKEND == "anthropic":
        _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    _system_prompt = Path(system_prompt_path).read_text(encoding="utf-8")


async def _complete_ollama(messages: list[dict], session_id: str) -> tuple[str, list[str]]:
    """Send messages to Ollama via its OpenAI-compatible endpoint."""
    with tracer.start_as_current_span("llm.call_ollama") as span:
        span.set_attribute("llm.model", OLLAMA_MODEL)
        span.set_attribute("kapampangan.session_id", session_id)
        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{OLLAMA_URL}/v1/chat/completions",
                    json={
                        "model": OLLAMA_MODEL,
                        "messages": [{"role": "system", "content": _system_prompt}] + messages,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"]["content"]
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise
        span.set_attribute("llm.duration_seconds", time.time() - t0)
        return text, []


async def complete(messages: list[dict], session_id: str = "") -> tuple[str, list[str]]:
    """
    Send messages to Claude, handle any tool calls, and return:
      (response_text, list_of_tool_names_used)

    Implements the agentic loop: Claude may request tool calls, we execute
    them, return results, and Claude produces a final text response.
    """
    if BACKEND == "ollama":
        return await _complete_ollama(messages, session_id)

    client = _client
    system_prompt = _system_prompt
    tool_definitions = get_tool_definitions()
    tools_used: list[str] = []

    current_messages = list(messages)

    with tracer.start_as_current_span("llm.assemble_request") as assemble_span:
        assemble_span.set_attribute("kapampangan.session_id", session_id)
        try:
            while True:
                with tracer.start_as_current_span("llm.call_anthropic") as llm_span:
                    llm_span.set_attribute("llm.model", MODEL)
                    llm_span.set_attribute("llm.max_tokens", MAX_TOKENS)
                    t0 = time.time()
                    try:
                        response = await client.messages.create(
                            model=MODEL,
                            max_tokens=MAX_TOKENS,
                            system=system_prompt,
                            tools=tool_definitions,
                            messages=current_messages,
                        )
                    except Exception as e:
                        llm_span.set_status(StatusCode.ERROR, str(e))
                        llm_span.record_exception(e)
                        raise

                    llm_duration = time.time() - t0
                    llm_span.set_attribute("llm.input_tokens", response.usage.input_tokens)
                    llm_span.set_attribute("llm.output_tokens", response.usage.output_tokens)
                    llm_span.set_attribute("llm.stop_reason", response.stop_reason)

                    ctx = llm_span.get_span_context()
                    exemplar = {"TraceID": trace.format_trace_id(ctx.trace_id)} if ctx.is_valid else None
                    LLM_CALL_DURATION.labels(model=MODEL).observe(llm_duration, exemplar=exemplar)
                    LLM_TOKENS_TOTAL.labels(direction="input", model=MODEL).inc(
                        response.usage.input_tokens, exemplar=exemplar
                    )
                    LLM_TOKENS_TOTAL.labels(direction="output", model=MODEL).inc(
                        response.usage.output_tokens, exemplar=exemplar
                    )

                if response.stop_reason == "end_turn":
                    text = "".join(
                        block.text
                        for block in response.content
                        if hasattr(block, "text")
                    )
                    assemble_span.set_attribute("kapampangan.tools_used_count", len(tools_used))
                    return text, tools_used

                if response.stop_reason == "tool_use":
                    tool_calls = [b for b in response.content if b.type == "tool_use"]
                    assemble_span.set_attribute("kapampangan.tools_requested", len(tool_calls))
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
                text = "".join(
                    block.text for block in response.content if hasattr(block, "text")
                )
                return text, tools_used

        except Exception as e:
            assemble_span.set_status(StatusCode.ERROR, str(e))
            assemble_span.record_exception(e)
            raise
