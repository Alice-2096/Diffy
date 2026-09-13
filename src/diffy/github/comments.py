from __future__ import annotations

from typing import Protocol


class ReviewPublisher(Protocol):
    def publish(self, pull_request: int, markdown: str) -> None: ...
