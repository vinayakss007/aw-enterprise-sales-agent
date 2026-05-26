"""CRM adapter behaviour and factory selection."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_mock_adapter_upsert_idempotent_per_email():
    from app.integrations.crm.mock import MockCRMAdapter

    adapter = MockCRMAdapter()
    a = await adapter.upsert_contact(email="alice@example.com", name="Alice")
    b = await adapter.upsert_contact(email="alice@example.com", name="Alice Updated")
    assert a.id == b.id
    assert b.name == "Alice Updated"


@pytest.mark.asyncio
async def test_mock_adapter_search_and_get():
    from app.integrations.crm.mock import MockCRMAdapter

    adapter = MockCRMAdapter()
    contact = await adapter.upsert_contact(
        email="bob@example.com", name="Bob", company="Bobco"
    )
    found = await adapter.search_contact_by_email("BOB@example.com")
    assert found is not None
    assert found.id == contact.id
    fetched = await adapter.get_contact(contact.id)
    assert fetched is not None
    assert fetched.company == "Bobco"


@pytest.mark.asyncio
async def test_mock_adapter_notes():
    from app.integrations.crm.base import CRMError
    from app.integrations.crm.mock import MockCRMAdapter

    adapter = MockCRMAdapter()
    contact = await adapter.upsert_contact(email="c@example.com")
    note_id = await adapter.create_note(contact.id, "rang the bell")
    assert note_id
    assert adapter.notes_for(contact.id)[0]["content"] == "rang the bell"

    with pytest.raises(CRMError):
        await adapter.create_note("not-a-real-id", "lost note")


def test_factory_returns_mock_by_default():
    from app.integrations.crm.factory import get_crm_adapter
    from app.integrations.crm.mock import MockCRMAdapter

    assert isinstance(get_crm_adapter(None), MockCRMAdapter)
    assert isinstance(get_crm_adapter({}), MockCRMAdapter)
    assert isinstance(get_crm_adapter({"crm": {"provider": "mock"}}), MockCRMAdapter)


def test_factory_picks_hubspot_when_token_present():
    from app.integrations.crm.factory import get_crm_adapter
    from app.integrations.crm.hubspot import HubSpotCRMAdapter

    adapter = get_crm_adapter(
        {
            "crm": {
                "provider": "hubspot",
                "credentials": {"access_token": "pat-fake"},
            }
        }
    )
    assert isinstance(adapter, HubSpotCRMAdapter)
    assert adapter.provider == "hubspot"


def test_factory_falls_back_when_hubspot_missing_token():
    from app.integrations.crm.factory import get_crm_adapter
    from app.integrations.crm.mock import MockCRMAdapter

    adapter = get_crm_adapter({"crm": {"provider": "hubspot"}})
    assert isinstance(adapter, MockCRMAdapter)


def test_factory_falls_back_for_unknown_provider():
    from app.integrations.crm.factory import get_crm_adapter
    from app.integrations.crm.mock import MockCRMAdapter

    adapter = get_crm_adapter({"crm": {"provider": "salesforce-but-not-implemented"}})
    assert isinstance(adapter, MockCRMAdapter)


@pytest.mark.asyncio
async def test_crm_service_uses_injected_adapter():
    from types import SimpleNamespace

    from app.integrations.crm.mock import MockCRMAdapter
    from app.services.customer.crm_integration import CRMIntegrationService

    adapter = MockCRMAdapter()
    service = CRMIntegrationService(tenant_id="t1", adapter=adapter)
    fake_lead = SimpleNamespace(
        id="l1",
        email="lead@target.test",
        name="Lead",
        company="Target",
        linkedin_url=None,
    )
    contact_id = await service.sync_lead_to_crm(fake_lead)
    assert contact_id and contact_id.startswith("mock_")

    note_id = await service.create_note_in_crm(contact_id, "hello")
    assert note_id and note_id.startswith("mock_note_")


@pytest.mark.asyncio
async def test_hubspot_adapter_search_uses_v3_search_endpoint():
    """The skeleton talks to /crm/v3/objects/contacts/search with an EQ filter."""
    import httpx

    from app.integrations.crm.hubspot import HubSpotCRMAdapter

    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.read()
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "999",
                        "properties": {
                            "email": "carol@target.test",
                            "firstname": "Carol",
                            "lastname": "Carlson",
                            "company": "Target",
                        },
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = HubSpotCRMAdapter(access_token="pat-fake", client=client)
        contact = await adapter.search_contact_by_email("carol@target.test")

    assert contact is not None
    assert contact.id == "999"
    assert contact.name == "Carol Carlson"
    assert "/crm/v3/objects/contacts/search" in captured["url"]
    assert b"carol@target.test" in captured["body"]
