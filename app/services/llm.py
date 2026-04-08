"""
Anthropic API call assembly and execution.

Each call is stateless from the LLM's perspective. This service:
  1. Loads the system prompt from config/system_prompt.md
  2. Receives the conversation history from history.py
  3. Appends tool results when Claude has made tool calls
  4. Returns the final text response and a list of tool names used
"""

import os
from pathlib import Path
import anthropic
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from .tool_router import get_tool_definitions, dispatch

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024
SYSTEM_PROMPT_PATH = "/app/config/system_prompt.md"

_client: anthropic.AsyncAnthropic | None = None
_system_prompt: str | None = None

tracer = trace.get_tracer(__name__)


def init(system_prompt_path: str = SYSTEM_PROMPT_PATH) -> None:
    """Initialise the Anthropic client and load the system prompt. Call once at startup."""
    global _client, _system_prompt
    _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    _system_prompt = Path(system_prompt_path).read_text(encoding="utf-8")


async def complete(messages: list[dict], session_id: str = "") -> tuple[str, list[str]]:
    """
    Send messages to Claude, handle any tool calls, and return:
      (response_text, list_of_tool_names_used)

    Implements the agentic loop: Claude may request tool calls, we execute
    them, return results, and Claude produces a final text response.
    """
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

                    llm_span.set_attribute("llm.input_tokens", response.usage.input_tokens)
                    llm_span.set_attribute("llm.output_tokens", response.usage.output_tokens)
                    llm_span.set_attribute("llm.stop_reason", response.stop_reason)

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
