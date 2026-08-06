"""Embedding + ChromaDB write side for the embed pipeline.

Wraps a local Sentence-Transformers model and the Chroma collection. Embeddings
are L2-normalized so nearest-neighbour by the collection's default distance
matches cosine order — the backend reads with the *same* model and the same
normalization, so query and document vectors live in one space.

Writes use `collection.upsert(...)`, keyed by the deterministic doc ids from
`summaries.py`, so re-running the pipeline overwrites in place rather than
duplicating.
"""

from __future__ import annotations

from functools import cached_property
from typing import Any

from common.config import settings


class Embedder:
    """Local embedding model + Chroma collection accessor (lazy-loaded)."""

    @cached_property
    def _model(self):
        # Imported lazily so `import embed.embedder` doesn't pull in torch.
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(settings.embedding_model)

    @cached_property
    def _collection(self):
        import chromadb

        client = chromadb.HttpClient(
            host=settings.chroma_host, port=settings.chroma_port
        )
        return client.get_or_create_collection(name=settings.chroma_collection)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of strings into normalized float vectors."""
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert vectors + source text + metadata into Chroma by id."""
        if not ids:
            return
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def count(self) -> int:
        return self._collection.count()
