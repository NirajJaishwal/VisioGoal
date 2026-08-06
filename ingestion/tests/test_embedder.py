"""Tests for bounded Chroma write batches."""

from embed.embedder import Embedder


class FakeCollection:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def upsert(self, **kwargs) -> None:
        self.calls.append(kwargs)


def test_upsert_splits_parallel_inputs_into_configured_batches() -> None:
    embedder = Embedder(batch_size=2)
    collection = FakeCollection()
    embedder.__dict__["_collection"] = collection
    ids = ["a", "b", "c", "d", "e"]

    embedder.upsert(
        ids=ids,
        embeddings=[[float(index)] for index in range(len(ids))],
        documents=[f"document {index}" for index in range(len(ids))],
        metadatas=[{"index": index} for index in range(len(ids))],
    )

    assert [call["ids"] for call in collection.calls] == [["a", "b"], ["c", "d"], ["e"]]
    assert [item for call in collection.calls for item in call["ids"]] == ids
