from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class KnowledgeChunk:
    id: str
    text: str
    source: str
    source_type: str
    authority: str
    section: str | None = None
    technology: str | None = None
    service: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
