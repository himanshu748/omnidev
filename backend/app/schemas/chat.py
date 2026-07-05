"""Schemas for the streaming chat endpoint and conversation sessions."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    system: str | None = Field(default=None, max_length=4000)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    # Continue an existing conversation; omit to start fresh (a new session
    # id is created and returned as the stream's first event).
    session_id: str | None = Field(default=None, max_length=64)
    # Let the model call tools from enabled MCP servers (local provider only).
    use_tools: bool = False


class SessionInfo(BaseModel):
    id: str
    title: str = ""
    created_at: str = ""
    updated_at: str = ""
    message_count: int = 0


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]


class SessionMessage(BaseModel):
    role: str
    content: str
    created_at: str = ""


class SessionMessagesResponse(BaseModel):
    session_id: str
    messages: list[SessionMessage]
