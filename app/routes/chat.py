import json
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from opentelemetry import trace
from opentelemetry import context as otel_context

from models.schemas import ChatRequest
from services import llm
from metrics import LLM_ERRORS_TOTAL

router = APIRouter(tags=["chat"])

tracer = trace.get_tracer(__name__)


@router.post(
    "/chat",
    summary="Send a conversation turn",
    response_description=(
        "Server-sent events stream. Each event is `data: {\"text\": \"...\"}`. "
        "The stream ends with `data: [DONE]`."
    ),
)
async def chat(request: ChatRequest):
    """
    Accepts the full conversation history and streams the assistant response
    as Server-Sent Events (SSE).

    Each SSE frame carries `{"text": "..."}`. The final frame is `[DONE]`.

    The agentic loop runs inside this call: the LLM may invoke `vocabulary_lookup`
    or `grammar_lookup` tool calls before producing the final response. Tool
    results are not streamed; only the final assistant text is sent.

    If the response was produced without verified tool data, it is prefixed with
    an uncertainty caveat.
    """
    session_id = request.session_id or str(uuid.uuid4())
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Capture context now — the HTTP request span closes when we return
    # StreamingResponse, before the generator runs.
    ctx = otel_context.get_current()

    _UNVERIFIED_CAVEAT = (
        "⚠️ *Training knowledge only — not verified against reference data. "
        "Treat this as a best effort and check with a native speaker if precision matters.*\n\n"
    )

    async def stream():
        with tracer.start_as_current_span("chat.stream", context=ctx):
            try:
                response_text, tools_used = await llm.complete(messages, session_id=session_id)
                # If the model answered without any tool calls, prepend the caveat
                # unless it already included one (model followed the instruction itself).
                if not tools_used and "training knowledge" not in response_text.lower():
                    response_text = _UNVERIFIED_CAVEAT + response_text
                yield f"data: {json.dumps({'text': response_text})}\n\n"
            except Exception as e:
                LLM_ERRORS_TOTAL.labels(
                    backend=llm.ACTIVE_BACKEND,
                    model=llm.ACTIVE_MODEL,
                ).inc()
                yield f"data: {json.dumps({'text': f'Error: {e}'})}\n\n"
            finally:
                yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    """No-op kept for API compatibility — history is owned by the frontend."""
    return {"session_id": session_id, "cleared": True}
