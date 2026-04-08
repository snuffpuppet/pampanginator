from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from models.schemas import ChatRequest, ChatResponse
from services import history, llm

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle one conversation turn.

    Retrieves session history, appends the new user message, calls the LLM
    (which may trigger tool calls), appends the assistant response, and returns.
    """
    session_id = request.session_id
    user_message = request.message

    # Append user message to history
    history.append(session_id, "user", user_message)

    # Build message list for this API call
    messages = history.get_history(session_id)

    try:
        response_text, tools_used = await llm.complete(messages)
    except Exception as e:
        # Remove the user message we just appended so history stays consistent
        history.clear(session_id)
        raise HTTPException(status_code=500, detail=str(e))

    # Append assistant response to history
    history.append(session_id, "assistant", response_text)

    return ChatResponse(
        response=response_text,
        tools_used=tools_used,
        session_id=session_id,
    )


@router.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    """Clear the conversation history for a session."""
    history.clear(session_id)
    return {"session_id": session_id, "cleared": True}
