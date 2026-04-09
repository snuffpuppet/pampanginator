from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    session_id: str = ""


class ToolCall(BaseModel):
    name: str
    parameters: dict


class ToolResult(BaseModel):
    tool_name: str
    result: dict
    error: Optional[str] = None
