from __future__ import annotations


def markdown_sections(document: str) -> list[tuple[str | None, str]]:
    """Split Markdown on headings while retaining semantic sections."""
    sections: list[tuple[str | None, str]] = []
    heading: str | None = None
    body: list[str] = []

    for line in document.splitlines():
        if line.startswith("#"):
            if body and any(part.strip() for part in body):
                sections.append((heading, "\n".join(body).strip()))
            heading = line.lstrip("#").strip()
            body = []
        else:
            body.append(line)

    if body and any(part.strip() for part in body):
        sections.append((heading, "\n".join(body).strip()))
    return sections
