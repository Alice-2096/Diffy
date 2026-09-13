from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HistoricalPullRequest:
    number: int
    title: str
    summary: str
    files: tuple[str, ...]
    review_comments: tuple[str, ...]
    url: str
