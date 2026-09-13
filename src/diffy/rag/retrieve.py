from __future__ import annotations

from typing import Protocol

from diffy.rag.embeddings import Embedder
from diffy.rag.models import KnowledgeChunk
from diffy.rag.store import VectorStore


class Retriever(Protocol):
    """Allows Qdrant local mode to be replaced without changing review logic."""

    def search(
        self,
        query: str,
        *,
        source_types: tuple[str, ...],
        limit: int = 5,
    ) -> list[KnowledgeChunk]: ...


class LocalRetriever:
    def __init__(self, embedder: Embedder, store: VectorStore):
        self.embedder = embedder
        self.store = store

    def search(
        self,
        query: str,
        *,
        source_types: tuple[str, ...],
        limit: int = 5,
    ) -> list[KnowledgeChunk]:
        if not query.strip() or limit < 1:
            raise ValueError("Query must not be blank and limit must be positive")
        if not source_types:
            return []
        return self.store.search(
            self.embedder.encode_query(query),
            source_types=source_types,
            limit=limit,
        )
