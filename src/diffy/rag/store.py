from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict
from math import isfinite
from pathlib import Path
from typing import Protocol
from uuid import NAMESPACE_URL, uuid5

from diffy.rag.models import KnowledgeChunk


class VectorStore(Protocol):
    def upsert(
        self,
        chunks: Sequence[KnowledgeChunk],
        vectors: Sequence[Sequence[float]],
    ) -> None: ...

    def search(
        self,
        vector: Sequence[float],
        *,
        source_types: tuple[str, ...],
        limit: int,
    ) -> list[KnowledgeChunk]: ...

    def replace_source(
        self,
        source: str,
        chunks: Sequence[KnowledgeChunk],
        vectors: Sequence[Sequence[float]],
    ) -> None: ...


class QdrantLocalStore:
    """An on-disk, single-process collection; no Qdrant server or API key."""

    def __init__(
        self,
        path: Path,
        *,
        collection: str = "diffy-bge-small-en-v1_5",
        dimension: int = 384,
    ):
        if dimension < 1:
            raise ValueError("Vector dimension must be positive")
        try:
            from qdrant_client import QdrantClient, models
        except ImportError as exc:
            raise RuntimeError(
                "Install RAG dependencies: pip install -e '.[rag]'"
            ) from exc
        self._models = models
        self._client = QdrantClient(path=str(path))
        self.collection = collection
        self.dimension = dimension
        try:
            if not self._client.collection_exists(collection):
                self._client.create_collection(
                    collection_name=collection,
                    vectors_config=models.VectorParams(
                        size=dimension,
                        distance=models.Distance.COSINE,
                    ),
                )
            config = self._client.get_collection(collection).config.params.vectors
            if not isinstance(config, models.VectorParams) or (
                config.size != dimension or config.distance != models.Distance.COSINE
            ):
                raise ValueError("Collection has incompatible vector configuration")
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> QdrantLocalStore:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _validate(self, vector: Sequence[float]) -> list[float]:
        result = [float(value) for value in vector]
        if len(result) != self.dimension or not all(map(isfinite, result)):
            raise ValueError(
                "Vector must have the configured dimension and finite values"
            )
        if not any(result):
            raise ValueError("Cosine vectors must not be zero")
        return result

    @staticmethod
    def _point_id(chunk: KnowledgeChunk) -> str:
        return str(uuid5(NAMESPACE_URL, chunk.id))

    def upsert(
        self,
        chunks: Sequence[KnowledgeChunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Each chunk must have exactly one vector")
        if len({chunk.id for chunk in chunks}) != len(chunks):
            raise ValueError("Chunk IDs must be unique")
        points = [
            self._models.PointStruct(
                id=self._point_id(chunk),
                vector=self._validate(vector),
                payload=asdict(chunk),
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if points:
            self._client.upsert(self.collection, points=points, wait=True)

    def replace_source(
        self,
        source: str,
        chunks: Sequence[KnowledgeChunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        if any(chunk.source != source for chunk in chunks):
            raise ValueError("Replacement chunks must belong to the specified source")
        self.upsert(chunks, vectors)
        # Insert first so embedding/validation failures leave old evidence intact.
        self._client.delete(
            self.collection,
            points_selector=self._models.FilterSelector(
                filter=self._models.Filter(
                    must=[
                        self._models.FieldCondition(
                            key="source",
                            match=self._models.MatchValue(value=source),
                        )
                    ],
                    must_not=[
                        self._models.HasIdCondition(
                            has_id=[self._point_id(chunk) for chunk in chunks],
                        )
                    ]
                    if chunks
                    else None,
                ),
            ),
            wait=True,
        )

    def search(
        self,
        vector: Sequence[float],
        *,
        source_types: tuple[str, ...],
        limit: int = 5,
    ) -> list[KnowledgeChunk]:
        if limit < 1:
            raise ValueError("Search limit must be positive")
        if not source_types:
            return []
        response = self._client.query_points(
            self.collection,
            query=self._validate(vector),
            limit=limit,
            query_filter=self._models.Filter(
                must=[
                    self._models.FieldCondition(
                        key="source_type",
                        match=self._models.MatchAny(any=list(source_types)),
                    )
                ]
            ),
            with_payload=True,
            with_vectors=False,
        )
        return [KnowledgeChunk(**point.payload) for point in response.points]
