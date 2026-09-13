from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from diffy.rag.models import KnowledgeChunk
from diffy.review.findings import Finding


class LLMClient(Protocol):
    def review(
        self,
        *,
        diff: str,
        findings: Sequence[Finding],
        context: Sequence[KnowledgeChunk],
    ) -> str: ...
