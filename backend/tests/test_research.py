"""Tests for the research module."""
import pytest
from app.agents.sales_agent.research import (
    research_company, research_contact,
    _validate_email_format, _is_free_email,
)


class TestEmailValidation:
    def test_valid_email(self):
        assert _validate_email_format("user@example.com") is True

    def test_invalid_no_at(self):
        assert _validate_email_format("invalid") is False

    def test_invalid_empty(self):
        assert _validate_email_format("") is False

    def test_invalid_no_domain_dot(self):
        assert _validate_email_format("user@nodot") is False


class TestFreeEmail:
    def test_gmail_is_free(self):
        assert _is_free_email("gmail.com") is True

    def test_corporate_not_free(self):
        assert _is_free_email("acme.com") is False

    def test_case_insensitive(self):
        assert _is_free_email("Gmail.com") is True


@pytest.mark.asyncio
class TestResearchCompany:
    async def test_returns_domain(self):
        result = await research_company("acme.com")
        assert result["domain"] == "acme.com"
        assert result["website"] == "https://acme.com"

    async def test_infers_company_name(self):
        result = await research_company("big-corp.com")
        assert result["inferred_name"] == "Big Corp"

    async def test_empty_domain(self):
        result = await research_company("")
        assert "domain" in result


@pytest.mark.asyncio
class TestResearchContact:
    async def test_valid_business_email(self):
        result = await research_contact("john@acme.com", "John Smith")
        assert result["email_valid"] is True
        assert result["is_business_email"] is True
        assert result["first_name"] == "John"
        assert result["last_name"] == "Smith"

    async def test_free_email_detected(self):
        result = await research_contact("john@gmail.com")
        assert result["is_business_email"] is False

    async def test_domain_extracted(self):
        result = await research_contact("user@startup.io")
        assert result["domain"] == "startup.io"
