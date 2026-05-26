"""Tavily search provider (skeleton).

Implements ``SearchProvider`` against the Tavily Search API. Auth is a
simple bearer ``api_key`` POSTed in the JSON body — Tavily doesn't use
HTTP headers for the key.
"""
from __future__ import annotations

import logging

import httpx

from app.integrations.search.base import SearchError, SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class TavilySearchProvider(SearchProvider):
    provider = "tavily"

    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.tavily.com/search",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise SearchError("TavilySearchProvider requires an api_key")
        self._api_key = api_key
        self._endpoint = endpoint
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=15.0)

    async def search(self, query: str, *, limit: int = 5) -> list[SearchResult]:
        if not query or not query.strip():
            return []
        payload = {
            "api_key": self._api_key,
            "query": query.strip(),
            "search_depth": "basic",
            "max_results": max(1, min(limit, 20)),
            "include_answer": False,
        }
        try:
            response = await self._client.post(self._endpoint, json=payload)
        except httpx.HTTPError as exc:  # pragma: no cover — network defensive
            raise SearchError(f"Tavily transport error: {exc}") from exc
        if response.status_code >= 400:
            raise SearchError(
                f"Tavily search returned {response.status_code}: {response.text[:200]}"
            )
        body = response.json() or {}
        return [
            SearchResult(
                url=item.get("url") or "",
                title=item.get("title") or "",
                snippet=(item.get("content") or "")[:400],
                source="tavily",
                score=float(item.get("score", 0.0) or 0.0),
                extra={"raw": item},
            )
            for item in body.get("results", [])
            if item.get("url")
        ]

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()


__all__ = ["TavilySearchProvider"]
