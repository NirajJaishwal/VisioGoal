"""AI copilot endpoints — streamed chat, history, and readiness status.

`POST /api/v1/chat` streams the analyst's answer as Server-Sent Events so tokens
render in the UI as they are generated. Event stream shape:

    event: sources   data: {"sources": ["Premier League 2025 Standings", ...]}
    event: token     data: {"text": "Liverpool"}          (many)
    event: done      data: {"sources": [...]}
    event: error     data: {"message": "..."}              (instead of tokens)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Path
from fastapi.responses import StreamingResponse

from app.ai import service, vectorstore
from app.core.config import settings
from app.db.dependencies import DbSession
from app.schemas.chat import ChatMessageRead, ChatRequest, ChatStatus

router = APIRouter(prefix="/chat", tags=["chat"])

# Headers that keep the SSE stream flowing through proxies (Next rewrites,
# nginx) instead of being buffered until completion.
_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _sse(event: dict) -> str:
    """Format one service event as an SSE `event:`/`data:` frame."""
    return f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"


@router.post("", summary="Ask the football analyst (streamed)")
async def chat(session: DbSession, body: ChatRequest) -> StreamingResponse:
    """Stream a grounded, cited answer for the user's question."""

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for event in service.stream_turn(
                session, body.session_id, body.message
            ):
                yield _sse(event)
        except Exception:  # noqa: BLE001 - always close the stream with an error frame
            yield _sse(
                {
                    "type": "error",
                    "message": "The analyst hit an unexpected error. Please try again.",
                }
            )

    return StreamingResponse(
        event_stream(), media_type="text/event-stream", headers=_SSE_HEADERS
    )


@router.get(
    "/status",
    response_model=ChatStatus,
    summary="AI subsystem readiness (for verification)",
)
async def status() -> ChatStatus:
    """Report whether the LLM, Chroma, and embeddings are ready to serve."""
    try:
        embedded = vectorstore.count()
        chroma_ok = True
    except Exception:  # noqa: BLE001 - report Chroma unreachable instead of a 500
        embedded = 0
        chroma_ok = False

    return ChatStatus(
        llm_configured=settings.has_groq_key,
        chroma_reachable=chroma_ok,
        embedded_documents=embedded,
        provider="groq",
        model=settings.groq_model,
    )


@router.get(
    "/history/{session_id}",
    response_model=list[ChatMessageRead],
    summary="Replay a conversation's persisted turns",
)
async def history(
    session: DbSession,
    session_id: Annotated[str, Path(max_length=64, description="Conversation id.")],
) -> list[ChatMessageRead]:
    """Return every persisted turn for a session, oldest first."""
    return await service.get_history(session, session_id)
