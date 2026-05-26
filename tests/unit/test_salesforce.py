"""SalesforceCRMAdapter unit tests using httpx.MockTransport."""
from __future__ import annotations

import httpx
import pytest


@pytest.mark.asyncio
async def test_search_contact_returns_first_match():
    from app.integrations.crm.salesforce import SalesforceCRMAdapter

    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.read()
        return httpx.Response(
            200,
            json={
                "searchRecords": [
                    {
                        "Id": "003ABCDEFG",
                        "FirstName": "Carol",
                        "LastName": "Carlson",
                        "Email": "carol@target.test",
                        "Account": {"Name": "Target Inc"},
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = SalesforceCRMAdapter(
            access_token="bearer-fake",
            instance_url="https://example.my.salesforce.com",
            client=client,
        )
        contact = await adapter.search_contact_by_email("carol@target.test")

    assert contact is not None
    assert contact.id == "003ABCDEFG"
    assert contact.name == "Carol Carlson"
    assert contact.company == "Target Inc"
    assert "/services/data/v60.0/parameterizedSearch" in str(captured["url"])
    assert b"carol@target.test" in captured["body"]


@pytest.mark.asyncio
async def test_upsert_creates_new_contact_when_search_misses():
    """Empty search response → POST to /sobjects/Contact."""
    from app.integrations.crm.salesforce import SalesforceCRMAdapter

    posted: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "parameterizedSearch" in url:
            return httpx.Response(200, json={"searchRecords": []})
        if request.method == "POST" and "sobjects/Contact" in url:
            posted["body"] = request.read()
            return httpx.Response(
                201, json={"id": "003NEWID", "success": True, "errors": []}
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = SalesforceCRMAdapter(
            access_token="bearer-fake",
            instance_url="https://example.my.salesforce.com",
            client=client,
        )
        contact = await adapter.upsert_contact(
            email="newlead@target.test", name="New Lead"
        )

    assert contact.id == "003NEWID"
    assert contact.email == "newlead@target.test"
    assert b"newlead@target.test" in posted["body"]


@pytest.mark.asyncio
async def test_upsert_patches_existing_contact():
    """Search hit → PATCH /sobjects/Contact/{id}."""
    from app.integrations.crm.salesforce import SalesforceCRMAdapter

    patched: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "parameterizedSearch" in url:
            return httpx.Response(
                200,
                json={
                    "searchRecords": [
                        {
                            "Id": "003EXISTING",
                            "FirstName": "Old",
                            "LastName": "Name",
                            "Email": "x@target.test",
                        }
                    ]
                },
            )
        if request.method == "PATCH" and "/sobjects/Contact/003EXISTING" in url:
            patched["url"] = url
            patched["body"] = request.read()
            return httpx.Response(204)
        if "sobjects/Contact/003EXISTING" in url and request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "Id": "003EXISTING",
                    "FirstName": "Updated",
                    "LastName": "Name",
                    "Email": "x@target.test",
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = SalesforceCRMAdapter(
            access_token="bearer-fake",
            instance_url="https://example.my.salesforce.com",
            client=client,
        )
        contact = await adapter.upsert_contact(
            email="x@target.test", name="Updated Name"
        )

    assert contact.id == "003EXISTING"
    assert "url" in patched
    assert "/sobjects/Contact/003EXISTING" in str(patched["url"])
    assert b"Updated" in patched["body"]


@pytest.mark.asyncio
async def test_create_note_posts_to_note_sobject():
    from app.integrations.crm.salesforce import SalesforceCRMAdapter

    posted: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if request.method == "POST" and "sobjects/Note" in url:
            posted["body"] = request.read()
            return httpx.Response(201, json={"id": "00NNOTEID", "success": True})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = SalesforceCRMAdapter(
            access_token="bearer-fake",
            instance_url="https://example.my.salesforce.com",
            client=client,
        )
        note_id = await adapter.create_note("003ABC", "left voicemail")

    assert note_id == "00NNOTEID"
    body = (posted["body"] or b"").decode()
    assert "003ABC" in body
    assert "left voicemail" in body


def test_factory_picks_salesforce_when_configured():
    from app.integrations.crm.factory import get_crm_adapter
    from app.integrations.crm.salesforce import SalesforceCRMAdapter

    adapter = get_crm_adapter(
        {
            "crm": {
                "provider": "salesforce",
                "credentials": {
                    "access_token": "bearer-fake",
                    "instance_url": "https://example.my.salesforce.com",
                    "api_version": "v59.0",
                },
            }
        }
    )
    assert isinstance(adapter, SalesforceCRMAdapter)
    assert adapter.provider == "salesforce"
    assert adapter._api_version == "v59.0"


def test_factory_falls_back_when_salesforce_missing_creds():
    from app.integrations.crm.factory import get_crm_adapter
    from app.integrations.crm.mock import MockCRMAdapter

    # No instance_url.
    adapter = get_crm_adapter(
        {
            "crm": {
                "provider": "salesforce",
                "credentials": {"access_token": "x"},
            }
        }
    )
    assert isinstance(adapter, MockCRMAdapter)

    # No access_token.
    adapter = get_crm_adapter(
        {
            "crm": {
                "provider": "salesforce",
                "credentials": {"instance_url": "https://x.salesforce.com"},
            }
        }
    )
    assert isinstance(adapter, MockCRMAdapter)
