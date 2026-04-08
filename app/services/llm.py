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

from .tool_router import get_tool_definitions, dispatch

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024
SYSTEM_PROMPT_PATH = "/app/config/system_prompt.md"

_client: anthropic.AsyncAnthropic | None = None
_system_prompt: str | None = None


def init(system_prompt_path: str = SYSTEM_PROMPT_PATH) -> None:
    """Initialise the Anthropic client and load the system prompt. Call once at startup."""
    global _client, _system_prompt
    _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    _system_prompt = Path(system_prompt_path).read_text(encoding="utf-8")


async def complete(messages: list[dict]) -> tuple[str, list[str]]:
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

    while True:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            tools=tool_definitions,
            messages=current_messages,
        )

        if response.stop_reason == "end_turn":
            # Extract text from the response
            text = "".join(
                block.text
                for block in response.content
                if hasattr(block, "text")
            )
            return text, tools_used

        if response.stop_reason == "tool_use":
            # Collect all tool calls in this response
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tools_used.append(block.name)
                result = await dispatch(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })

            # Append assistant's tool_use message and our tool_result message
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
