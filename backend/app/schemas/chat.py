"""Chat API schemas — request body, persisted-message view, and status."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """A user's question plus the client-managed conversation id.

    `session_id` groups turns into a conversation (persisted in `chat_messages`);
    the client generates it once and reuses it across turns.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "8f14e45f-ceea-467e-9f0b-0e2a1c9d3f21",
                "message": "Why is Liverpool leading the Premier League?",
            }
        }
    )

    session_id: str = Field(
        min_length=1, max_length=64, description="Client-generated conversation id."
    )
    message: str = Field(
        min_length=1, max_length=2000, description="The user's question."
    )


class ChatMessageRead(BaseModel):
    """One persisted turn of a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str = Field(description='"user" or "assistant".')
    content: str
    created_at: datetime


class ChatStatus(BaseModel):
    """AI-subsystem readiness, used by the verification / health surface."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "llm_configured": True,
                "chroma_reachable": True,
                "embedded_documents": 142,
                "provider": "groq",
                "model": "llama-3.3-70b-versatile",
            }
        }
    )

    llm_configured: bool = Field(
        description="True when a real Groq key is set (streaming will work)."
    )
    chroma_reachable: bool = Field(description="True when the vector store responds.")
    embedded_documents: int = Field(
        description="Number of documents in the Chroma collection (0 until embedded)."
    )
    provider: str = Field(description="LLM provider serving the copilot.")
    model: str = Field(description="Model id the copilot streams from.")
