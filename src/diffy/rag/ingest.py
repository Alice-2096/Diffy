from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from diffy.rag.chunk import markdown_sections
from diffy.rag.embeddings import Embedder
from diffy.rag.models import KnowledgeChunk
from diffy.rag.store import VectorStore


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


def ingest_markdown(
    path: Path,
    *,
    source_type: str,
    authority: str,
    embedder: Embedder,
    store: VectorStore,
    split_text: Callable[[str], list[str]],
) -> int:
    """Refresh one document at a time, preserving source and authority metadata."""
    if not source_type.strip() or not authority.strip():
        raise ValueError("Source type and authority must not be blank")
    path = path.resolve(strict=True)
    paths = sorted(path.rglob("*.md")) if path.is_dir() else [path]
    if any(item.suffix.lower() != ".md" for item in paths):
        raise ValueError("Ingestion accepts Markdown files only")
    count = 0
    for document in paths:
        if document.is_symlink() or not document.is_file():
            continue
        chunks = [
            replace(chunk, id=f"{chunk.id}:{index}", text=text)
            for chunk in load_markdown(
                document,
                source_type=source_type,
                authority=authority,
            )
            for index, text in enumerate(split_text(chunk.text), start=1)
        ]
        vectors = embedder.encode([chunk.text for chunk in chunks])
        store.replace_source(document.as_posix(), chunks, vectors)
        count += len(chunks)
    return count
