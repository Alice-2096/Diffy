from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class Embedder(Protocol):
    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...
