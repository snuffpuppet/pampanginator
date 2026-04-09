import json
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from opentelemetry import trace
from opentelemetry import context as otel_context

from models.schemas import ChatRequest
from services import llm
from metrics import LLM_ERRORS_TOTAL

router = APIRouter()

tracer = trace.get_tracer(__name__)


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Receive a full message history from the frontend and stream the assistant
    response back as SSE.

    The span context is captured here, while the HTTP request span is still
    open, and propagated into the generator so that LLM child spans are
    correctly attached to this request's trace rather than becoming orphans.
    """
    session_id = request.session_id or str(uuid.uuid4())
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Capture context now — the HTTP request span closes when we return
    # StreamingResponse, before the generator runs.
    ctx = otel_context.get_current()

    async def stream():
        with tracer.start_as_current_span("chat.stream", context=ctx):
            try:
                response_text, _ = await llm.complete(messages, session_id=session_id)
                yield f"data: {json.dumps({'text': response_text})}\n\n"
            except Exception as e:
                LLM_ERRORS_TOTAL.labels(
                    backend=llm.BACKEND,
                    model=llm.OLLAMA_MODEL if llm.BACKEND == "ollama" else llm.MODEL,
                ).inc()
                yield f"data: {json.dumps({'text': f'Error: {e}'})}\n\n"
            finally:
                yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    """No-op kept for API compatibility — history is owned by the frontend."""
    return {"session_id": session_id, "cleared": True}
