"""Enrichment provider + factory unit tests."""
from __future__ import annotations

import httpx
import pytest


@pytest.mark.asyncio
async def test_fake_provider_is_deterministic():
    from app.integrations.enrichment.fake import FakeEnrichmentProvider

    provider = FakeEnrichmentProvider()
    a = await provider.enrich_by_domain("target.test")
    b = await provider.enrich_by_domain("target.test")
    assert a.to_dict() == b.to_dict()
    assert a.confidence == 0.4
    assert a.provider == "fake"
    assert a.industry  # non-empty
    assert a.employee_count and a.employee_count > 0
    assert a.company == "Target"


@pytest.mark.asyncio
async def test_fake_provider_different_domain_different_facts():
    from app.integrations.enrichment.fake import FakeEnrichmentProvider

    provider = FakeEnrichmentProvider()
    a = await provider.enrich_by_domain("target.test")
    b = await provider.enrich_by_domain("acme.test")
    # Different inputs almost certainly produce different industries OR sizes;
    # if they collide that's still legal but very unlikely.
    assert (a.industry, a.employee_count) != (b.industry, b.employee_count)


@pytest.mark.asyncio
async def test_fake_provider_strips_protocol_and_handles_empty():
    from app.integrations.enrichment.fake import FakeEnrichmentProvider

    provider = FakeEnrichmentProvider()
    a = await provider.enrich_by_domain("https://target.test")
    b = await provider.enrich_by_domain("target.test")
    assert a.industry == b.industry  # protocol stripped before hashing

    empty = await provider.enrich_by_domain("")
    assert empty.confidence == 0.0
    assert empty.company is None


@pytest.mark.asyncio
async def test_fake_provider_email_path_uses_domain():
    from app.integrations.enrichment.fake import FakeEnrichmentProvider

    provider = FakeEnrichmentProvider()
    by_email = await provider.enrich_by_email("alice@target.test")
    by_domain = await provider.enrich_by_domain("target.test")
    assert by_email.to_dict() == by_domain.to_dict()


@pytest.mark.asyncio
async def test_clearbit_provider_parses_company_response():
    from app.integrations.enrichment.clearbit import ClearbitEnrichmentProvider

    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(
            200,
            json={
                "id": "c-001",
                "name": "Target Inc",
                "domain": "target.test",
                "description": "A sample company",
                "category": {"industry": "Software"},
                "metrics": {"employees": 250, "annualRevenue": 12_000_000},
                "geo": {"city": "Austin", "country": "USA"},
                "linkedin": {"handle": "company/target"},
                "twitter": {"handle": "target"},
                "tech": ["python", "postgres"],
                "tags": ["b2b"],
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = ClearbitEnrichmentProvider(api_key="sk-fake", client=client)
        facts = await provider.enrich_by_domain("target.test")

    assert facts.company == "Target Inc"
    assert facts.industry == "Software"
    assert facts.employee_count == 250
    assert facts.annual_revenue == 12_000_000
    assert facts.headquarters == "Austin, USA"
    assert facts.website == "https://target.test"
    assert facts.linkedin_url == "company/target"
    assert facts.twitter_handle == "target"
    assert "python" in facts.technologies
    assert facts.confidence == 0.9
    assert facts.extra == {"clearbit_id": "c-001"}
    assert "domain=target.test" in str(captured["url"])
    # HTTP basic auth header is base64-encoded
    assert captured["auth"] and captured["auth"].startswith("Basic ")


@pytest.mark.asyncio
async def test_clearbit_returns_zero_confidence_on_404():
    from app.integrations.enrichment.clearbit import ClearbitEnrichmentProvider

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = ClearbitEnrichmentProvider(api_key="sk-fake", client=client)
        facts = await provider.enrich_by_domain("missing.test")

    assert facts.confidence == 0.0
    assert facts.company is None


@pytest.mark.asyncio
async def test_clearbit_raises_on_5xx():
    from app.integrations.enrichment.base import EnrichmentError
    from app.integrations.enrichment.clearbit import ClearbitEnrichmentProvider

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream down")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = ClearbitEnrichmentProvider(api_key="sk-fake", client=client)
        with pytest.raises(EnrichmentError):
            await provider.enrich_by_domain("flaky.test")


def test_factory_default_is_fake():
    from app.integrations.enrichment.factory import get_enrichment_provider
    from app.integrations.enrichment.fake import FakeEnrichmentProvider

    assert isinstance(get_enrichment_provider(None), FakeEnrichmentProvider)
    assert isinstance(get_enrichment_provider({}), FakeEnrichmentProvider)


def test_factory_picks_clearbit_when_configured():
    from app.integrations.enrichment.clearbit import ClearbitEnrichmentProvider
    from app.integrations.enrichment.factory import get_enrichment_provider

    provider = get_enrichment_provider(
        {
            "enrichment": {
                "provider": "clearbit",
                "credentials": {"api_key": "sk-real"},
            }
        }
    )
    assert isinstance(provider, ClearbitEnrichmentProvider)


def test_factory_falls_back_when_clearbit_missing_key():
    from app.integrations.enrichment.factory import get_enrichment_provider
    from app.integrations.enrichment.fake import FakeEnrichmentProvider

    provider = get_enrichment_provider(
        {"enrichment": {"provider": "clearbit", "credentials": {}}}
    )
    assert isinstance(provider, FakeEnrichmentProvider)
