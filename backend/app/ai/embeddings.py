"""Local sentence-transformers embeddings.

The same model (and normalization) must be used when embedding documents during
ingestion and when embedding a query here, or similarity search is meaningless.
Embeddings are L2-normalized so nearest-neighbour by L2 distance matches cosine
order — avoiding any Chroma version-specific distance-space configuration.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings


@lru_cache(maxsize=1)
def _model():
    # Imported lazily so importing this module doesn't pull in torch eagerly.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def embed_text(text: str) -> list[float]:
    """Embed a single string into a normalized float vector."""
    vector = _model().encode(text, normalize_embeddings=True)
    return vector.tolist()
