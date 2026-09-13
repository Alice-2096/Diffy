from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class Finding:
    category: str
    severity: Severity
    title: str
    evidence: str
    recommendation: str
    file: str | None = None
    diff_line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
