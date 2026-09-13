from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReviewEvidence:
    source: str
    section: str | None = None


@dataclass(frozen=True, slots=True)
class ReviewResult:
    summary: str
    risk: str
    findings: tuple[str, ...]
    evidence: tuple[ReviewEvidence, ...]
