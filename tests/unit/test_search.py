"""Search provider + factory unit tests."""
from __future__ import annotations

import httpx
import pytest


@pytest.mark.asyncio
async def test_fake_search_is_deterministic_and_caps_to_limit():
    from app.integrations.search.fake import FakeSearchProvider

    provider = FakeSearchProvider()
    a = await provider.search("Target Inc", limit=3)
    b = await provider.search("Target Inc", limit=3)
    assert [r.url for r in a] == [r.url for r in b]
    assert len(a) == 3
    # Scores monotonically decreasing.
    assert all(a[i].score >= a[i + 1].score for i in range(len(a) - 1))


@pytest.mark.asyncio
async def test_fake_search_handles_empty_query():
    from app.integrations.search.fake import FakeSearchProvider

    assert await FakeSearchProvider().search("") == []
    assert await FakeSearchProvider().search("   ") == []


@pytest.mark.asyncio
async def test_tavily_search_parses_results():
    from app.integrations.search.tavily import TavilySearchProvider

    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.read()
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "url": "https://example.com/1",
                        "title": "First",
                        "content": "Snippet one",
                        "score": 0.92,
                    },
                    {
                        "url": "https://example.com/2",
                        "title": "Second",
                        "content": "Snippet two",
                        "score": 0.71,
                    },
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = TavilySearchProvider(api_key="sk-fake", client=client)
        results = await provider.search("acme corp", limit=2)

    assert len(results) == 2
    assert results[0].url == "https://example.com/1"
    assert results[0].score == 0.92
    assert results[0].source == "tavily"
    body = (captured["body"] or b"").decode()
    assert '"query":"acme corp"' in body
    assert '"max_results":2' in body


@pytest.mark.asyncio
async def test_tavily_drops_results_without_url():
    """Tavily occasionally returns sparse results; we filter them out."""
    from app.integrations.search.tavily import TavilySearchProvider

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {"url": "https://ok.example.com/", "title": "OK"},
                    {"url": "", "title": "missing url"},
                    {"url": None, "title": "null url"},
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = TavilySearchProvider(api_key="sk-fake", client=client)
        results = await provider.search("anything")
    assert len(results) == 1
    assert results[0].title == "OK"


@pytest.mark.asyncio
async def test_tavily_raises_on_5xx():
    from app.integrations.search.base import SearchError
    from app.integrations.search.tavily import TavilySearchProvider

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream down")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = TavilySearchProvider(api_key="sk-fake", client=client)
        with pytest.raises(SearchError):
            await provider.search("anything")


def test_factory_default_is_fake():
    from app.integrations.search.factory import get_search_provider
    from app.integrations.search.fake import FakeSearchProvider

    assert isinstance(get_search_provider(None), FakeSearchProvider)
    assert isinstance(get_search_provider({}), FakeSearchProvider)


def test_factory_picks_tavily_when_configured():
    from app.integrations.search.factory import get_search_provider
    from app.integrations.search.tavily import TavilySearchProvider

    provider = get_search_provider(
        {"search": {"provider": "tavily", "credentials": {"api_key": "sk-real"}}}
    )
    assert isinstance(provider, TavilySearchProvider)


def test_factory_falls_back_when_tavily_missing_key():
    from app.integrations.search.factory import get_search_provider
    from app.integrations.search.fake import FakeSearchProvider

    provider = get_search_provider(
        {"search": {"provider": "tavily", "credentials": {}}}
    )
    assert isinstance(provider, FakeSearchProvider)
