from __future__ import annotations

from typing import Any, Protocol


class GitHubClient(Protocol):
    """Minimal API needed by collectors and comment publishers."""

    def pull_request(self, number: int) -> dict[str, Any]: ...

    def pull_request_files(self, number: int) -> list[dict[str, Any]]: ...

    def pull_request_comments(self, number: int) -> list[dict[str, Any]]: ...
