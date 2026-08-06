"""Groq client — the only place that talks to the LLM.

Exposes an async token stream. Groq serves an OpenAI-style chat-completions API,
where the system prompt is the first entry in `messages` (`role: "system"`)
rather than a separate top-level argument. `stream_answer` keeps that wire detail
here, so the service layer just passes a system string plus the turn list and
swapping providers stays a one-file change.

Temperature is held low: this is a grounded analyst that must restate retrieved
statistics faithfully, not write creatively.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from app.core.config import settings

# Low but non-zero: keeps numbers faithful while allowing readable prose.
_TEMPERATURE = 0.2


class LLMConfigError(RuntimeError):
    """Raised when the Groq key is missing or a placeholder."""


@lru_cache(maxsize=1)
def _client():
    from groq import AsyncGroq

    return AsyncGroq(api_key=settings.groq_api_key)


async def stream_answer(
    system: str, messages: list[dict[str, str]]
) -> AsyncIterator[str]:
    """Yield answer text deltas from the model for the given conversation."""
    if not settings.has_groq_key:
        raise LLMConfigError(
            "GROQ_API_KEY is not set to a real key. Add a valid key to .env "
            "to enable live answers."
        )

    stream = await _client().chat.completions.create(
        model=settings.groq_model,
        max_tokens=settings.chat_max_tokens,
        temperature=_TEMPERATURE,
        messages=[{"role": "system", "content": system}, *messages],
        stream=True,
    )

    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
