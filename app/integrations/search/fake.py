"""Deterministic offline search provider.

Used in tests and as the default in dev environments where no real search
key is configured. Hashes the query into a small set of plausible-looking
"results" so downstream code can be tested without a network call.
"""
from __future__ import annotations

import hashlib

from app.integrations.search.base import SearchProvider, SearchResult

_TOPIC_TEMPLATES = (
    ("https://news.example.com/{slug}", "{slug} announces Q3 results"),
    ("https://blog.example.com/{slug}", "Why {slug} is investing in AI"),
    (
        "https://crunchbase.example.com/{slug}",
        "{slug} raises Series B for sales automation",
    ),
    (
        "https://prodhunt.example.com/{slug}",
        "{slug} launches new product line",
    ),
    ("https://linkedin.example.com/{slug}", "{slug} hires new VP of Sales"),
)


def _slug(query: str) -> str:
    return query.lower().strip().replace(" ", "-")[:48] or "topic"


class FakeSearchProvider(SearchProvider):
    provider = "fake"

    async def search(self, query: str, *, limit: int = 5) -> list[SearchResult]:
        if not query or not query.strip():
            return []
        slug = _slug(query)
        # SHA-256 first byte picks the starting offset so the same query
        # always returns the same ordering.
        h = hashlib.sha256(query.encode("utf-8")).digest()
        offset = h[0] % len(_TOPIC_TEMPLATES)
        results: list[SearchResult] = []
        for i in range(min(limit, len(_TOPIC_TEMPLATES))):
            url_tpl, title_tpl = _TOPIC_TEMPLATES[(offset + i) % len(_TOPIC_TEMPLATES)]
            results.append(
                SearchResult(
                    url=url_tpl.format(slug=slug),
                    title=title_tpl.format(slug=slug.title()),
                    snippet=(
                        f"This is a synthetic excerpt about {slug} produced by the "
                        f"fake search provider for testing."
                    ),
                    source="fake",
                    # Score decays linearly with position so callers can sort.
                    score=round(1.0 - i * 0.1, 2),
                )
            )
        return results

    async def close(self) -> None:
        return None


__all__ = ["FakeSearchProvider"]
