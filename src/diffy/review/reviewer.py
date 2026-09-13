from __future__ import annotations

from dataclasses import dataclass

from diffy.analyzers.base import Analyzer
from diffy.review.findings import Finding


@dataclass(slots=True)
class Reviewer:
    analyzers: tuple[Analyzer, ...]

    def review(self, content: str) -> list[Finding]:
        return [
            finding
            for analyzer in self.analyzers
            for finding in analyzer.analyze(content)
        ]
