from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from diffy.rag.models import KnowledgeChunk


class VectorStore(Protocol):
    def upsert(
        self,
        chunks: Sequence[KnowledgeChunk],
        vectors: Sequence[Sequence[float]],
    ) -> None: ...
