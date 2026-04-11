import json
import os
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from opentelemetry import trace
from opentelemetry import context as otel_context

from models.schemas import ChatRequest
from services import llm, interactions as interaction_svc
from metrics import LLM_ERRORS_TOTAL

router = APIRouter(tags=["chat"])

tracer = trace.get_tracer(__name__)


@router.post(
    "/chat",
    summary="Send a conversation turn",
    response_description=(
        "Server-sent events stream. Each event is `data: {\"text\": \"...\"}`. "
        "The final event before [DONE] is `data: {\"interaction_id\": \"uuid\"}`. "
        "The stream ends with `data: [DONE]`."
    ),
)
async def chat(request: ChatRequest):
    """
    Accepts the full conversation history and streams the assistant response
    as Server-Sent Events (SSE).

    Each SSE frame carries `{"text": "..."}`. After the final text frame,
    one metadata frame carries `{"interaction_id": "uuid"}` so the frontend
    can attach feedback to the correct interaction record.
    The stream closes with `[DONE]`.

    The agentic loop runs inside: the LLM may invoke `vocabulary_lookup` or
    `grammar_lookup` before producing the final response. Only the final
    assistant text is streamed.
    """
    session_id = request.session_id or str(uuid.uuid4())
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    user_message = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )

    ctx = otel_context.get_current()

    _UNVERIFIED_CAVEAT = (
        "⚠️ *Training knowledge only — not verified against reference data. "
        "Treat this as a best effort and check with a native speaker if precision matters.*\n\n"
    )

    async def stream():
        with tracer.start_as_current_span("chat.stream", context=ctx):
            interaction_id = None
            try:
                response_text, tools_used = await llm.complete(messages, session_id=session_id)

                if not tools_used and "training knowledge" not in response_text.lower():
                    response_text = _UNVERIFIED_CAVEAT + response_text

                yield f"data: {json.dumps({'text': response_text})}\n\n"

                # Log the interaction and emit the interaction_id so the
                # frontend can attach feedback to this specific turn.
                try:
                    interaction_id = await interaction_svc.log_interaction(
                        session_id=session_id,
                        user_message=user_message,
                        llm_response=response_text,
                        model=llm.ACTIVE_MODEL,
                        system_prompt_version=llm.SYSTEM_PROMPT_VERSION,
                        tools_used=tools_used,
                    )
                    yield f"data: {json.dumps({'interaction_id': interaction_id})}\n\n"
                except Exception as log_err:
                    # Logging failure must never break the user-facing response
                    import logging
                    logging.getLogger(__name__).error(
                        "interaction logging failed", extra={"error": str(log_err)}
                    )

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


@router.get("/status", summary="Backend configuration status")
async def status():
    """Returns the active backend and model names for display in the UI."""
    return {
        "backend": llm.ACTIVE_BACKEND,
        "modelA": llm.ACTIVE_MODEL,
        "modelB": llm.ACTIVE_MODEL_B,
        "hasOpenRouterKey": bool(os.getenv("OPENROUTER_API_KEY", "")),
    }


@router.post("/chat/model-a", summary="Chat using model A")
async def chat_model_a(request: ChatRequest):
    """Stream a response using the primary model (ACTIVE_MODEL from llm.yaml)."""
    return await _chat_with_model(request, llm.ACTIVE_MODEL)


@router.post("/chat/model-b", summary="Chat using model B")
async def chat_model_b(request: ChatRequest):
    """Stream a response using the comparison model (model_b from llm.yaml)."""
    return await _chat_with_model(request, llm.ACTIVE_MODEL_B)


async def _chat_with_model(request: ChatRequest, model: str):
    session_id = request.session_id or str(uuid.uuid4())
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    ctx = otel_context.get_current()

    async def stream():
        with tracer.start_as_current_span("chat.stream", context=ctx):
            try:
                response_text, _ = await llm.complete_with_model(
                    messages, model=model, session_id=session_id
                )
                yield f"data: {json.dumps({'text': response_text})}\n\n"
            except Exception as e:
                LLM_ERRORS_TOTAL.labels(
                    backend=llm.ACTIVE_BACKEND,
                    model=model,
                ).inc()
                yield f"data: {json.dumps({'text': f'Error: {e}'})}\n\n"
            finally:
                yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
