from __future__ import annotations

from pathlib import Path

from diffy.rag.chunk import markdown_sections
from diffy.rag.models import KnowledgeChunk


def load_markdown(
    path: Path,
    *,
    source_type: str,
    authority: str,
) -> list[KnowledgeChunk]:
    document = path.read_text(encoding="utf-8")
    return [
        KnowledgeChunk(
            id=f"{path.as_posix()}#{index}",
            text=text,
            source=path.as_posix(),
            source_type=source_type,
            authority=authority,
            section=heading,
        )
        for index, (heading, text) in enumerate(markdown_sections(document), start=1)
    ]
