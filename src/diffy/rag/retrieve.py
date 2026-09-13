from __future__ import annotations

from typing import Protocol

from diffy.rag.models import KnowledgeChunk


class Retriever(Protocol):
    """Allows Qdrant local mode to be replaced without changing review logic."""

    def search(
        self,
        query: str,
        *,
        source_types: tuple[str, ...],
        limit: int = 5,
    ) -> list[KnowledgeChunk]: ...
