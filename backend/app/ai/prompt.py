"""System prompt and message assembly for the football analyst copilot."""

from __future__ import annotations

SYSTEM_PROMPT = """You are a professional football analyst.

Answer questions ONLY using the statistics and facts provided in the supplied \
context. The context is drawn from a football database (league standings, team \
statistics, and match results).

Rules you must follow:
- Never invent statistics, scores, or facts that are not present in the context.
- If the information needed to answer is not in the context, clearly state that \
you don't have that data rather than guessing.
- Always explain your reasoning, citing the specific numbers from the context \
(e.g. points, goals, wins) that support your answer.
- Be concise, precise, and objective. Do not give betting advice or predictions.
"""


def build_user_message(query: str, context: str) -> str:
    """Combine retrieved context with the user's question into one user turn."""
    context = context.strip() or "(no relevant data was retrieved)"
    return (
        "Use the following retrieved football data as your only source of truth.\n\n"
        "=== CONTEXT ===\n"
        f"{context}\n"
        "=== END CONTEXT ===\n\n"
        f"Question: {query}"
    )
