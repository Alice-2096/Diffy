from __future__ import annotations

from typing import Protocol

from diffy.review.findings import Finding


class Analyzer(Protocol):
    """Contract implemented by deterministic analyzers."""

    def analyze(self, content: str) -> list[Finding]: ...
