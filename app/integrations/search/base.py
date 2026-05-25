"""Web search Protocol + shared types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class SearchError(Exception):
    """Raised when a search provider fails (transport, auth, rate limit)."""


@dataclass
class SearchResult:
    """A single hit. ``url`` and ``title`` are required; everything else
    is best-effort.
    """

    url: str
    title: str
    snippet: str = ""
    source: str = ""
    score: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "source": self.source,
            "score": self.score,
            "extra": dict(self.extra),
        }


@runtime_checkable
class SearchProvider(Protocol):
    provider: str

    async def search(self, query: str, *, limit: int = 5) -> list[SearchResult]: ...

    async def close(self) -> None: ...


__all__ = ["SearchError", "SearchProvider", "SearchResult"]
