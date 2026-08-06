"""ChromaDB accessor (read side).

Ingestion writes the collection; the API only ever reads from it. The collection
uses Chroma's default distance space with L2-normalized embeddings (see
`embeddings.py`), so no space configuration is required on either side.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import settings


@lru_cache(maxsize=1)
def _collection():
    import chromadb

    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    return client.get_or_create_collection(name=settings.chroma_collection)


def query(embedding: list[float], n_results: int) -> dict[str, Any]:
    """Return the top-N nearest documents for a query embedding."""
    return _collection().query(
        query_embeddings=[embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )


def count() -> int:
    """Number of embedded documents (used by health/verification)."""
    return _collection().count()
