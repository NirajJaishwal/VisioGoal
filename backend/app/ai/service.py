"""Chat service — orchestrates one grounded, streamed conversation turn.

Flow for a single question:

    persist user turn -> retrieve grounded context -> stream the model's answer
    (yielding sources first, then token deltas) -> persist assistant turn

The service yields structured events; the endpoint serializes them to SSE. Chat
history is persisted in `chat_messages` and replayed (capped) so follow-up
questions keep conversational context. Retrieval context is injected only into
the *current* user turn, never into stored history.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import chat, retriever
from app.ai.chat import LLMConfigError
from app.ai.prompt import SYSTEM_PROMPT, build_user_message
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatMessageRead

# How many prior turns to replay for conversational context (bounds token use).
_HISTORY_LIMIT = 10


async def get_history(
    session: AsyncSession, session_id: str
) -> list[ChatMessageRead]:
    """Return the full persisted conversation for a session, oldest first."""
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
    )
    return [ChatMessageRead.model_validate(m) for m in result.scalars()]


async def stream_turn(
    session: AsyncSession, session_id: str, message: str
) -> AsyncIterator[dict]:
    """Run one turn and yield events: `sources`, then many `token`, then `done`.

    On a configuration problem (no Groq key) an `error` event is yielded
    instead of tokens; the user turn is still persisted so history is complete.
    """
    # Prior turns become the conversation context (before we add this one).
    history = await _history_as_messages(session, session_id)

    # Persist the user's turn immediately so it survives even a failed answer.
    session.add(ChatMessage(session_id=session_id, role="user", content=message))
    await session.commit()

    # Ground the answer in structured + semantic retrieval.
    result = await retriever.retrieve(session, message)
    yield {"type": "sources", "sources": result.citations}

    messages = history + [
        {"role": "user", "content": build_user_message(message, result.context)}
    ]

    answer_parts: list[str] = []
    try:
        async for delta in chat.stream_answer(SYSTEM_PROMPT, messages):
            answer_parts.append(delta)
            yield {"type": "token", "text": delta}
    except LLMConfigError as exc:
        yield {"type": "error", "message": str(exc)}
        return

    answer = "".join(answer_parts).strip()
    if answer:
        session.add(
            ChatMessage(session_id=session_id, role="assistant", content=answer)
        )
        await session.commit()

    yield {"type": "done", "sources": result.citations}


async def _history_as_messages(
    session: AsyncSession, session_id: str
) -> list[dict[str, str]]:
    """Load the last N turns as chat-API-shaped `{role, content}` dicts."""
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.desc())
        .limit(_HISTORY_LIMIT)
    )
    recent = list(result.scalars())[::-1]  # back to chronological order
    return [{"role": m.role, "content": m.content} for m in recent]
