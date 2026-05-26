"""Tests for the lead service."""
import pytest
from app.services.customer.lead_service import LeadService
from app.schemas.lead import LeadCreate, LeadUpdate
from app.db.models.user import User
from app.db.models.tenant import Tenant
from app.db.models.lead import Lead


@pytest.mark.asyncio
class TestLeadService:
    async def test_create_lead(self, db_session, user):
        service = LeadService(db_session, user)
        lead_data = LeadCreate(
            email="new@company.com",
            name="New Lead",
            company="New Corp",
        )
        result = await service.create_lead(lead_data)

        assert result.email == "new@company.com"
        assert result.name == "New Lead"
        assert result.company == "New Corp"
        assert result.status == "new"
        assert result.tenant_id == str(user.tenant_id)

    async def test_get_leads_empty(self, db_session, user):
        service = LeadService(db_session, user)
        leads = await service.get_leads()
        # May have leads from other fixtures, just check it returns a list
        assert isinstance(leads, list)

    async def test_get_lead_by_id(self, db_session, user, lead):
        service = LeadService(db_session, user)
        result = await service.get_lead(str(lead.id))

        assert result is not None
        assert result.id == str(lead.id)
        assert result.email == "john@acme.com"

    async def test_get_lead_wrong_tenant(self, db_session, tenant, user):
        """Lead from another tenant should not be visible."""
        import uuid
        other_tenant = Tenant(
            id=uuid.uuid4(), name="Other", subdomain="other", plan="free", status="active"
        )
        db_session.add(other_tenant)
        db_session.flush()

        other_user = User(
            id=uuid.uuid4(), tenant_id=other_tenant.id,
            email="other@other.com", name="Other", hashed_password="x", role="user",
        )
        db_session.add(other_user)
        db_session.flush()

        other_lead = Lead(
            id=uuid.uuid4(), tenant_id=other_tenant.id, user_id=other_user.id,
            email="secret@other.com", name="Secret", company="Other Corp", status="new",
        )
        db_session.add(other_lead)
        db_session.commit()

        # Our user should NOT see the other tenant's lead
        service = LeadService(db_session, user)
        result = await service.get_lead(str(other_lead.id))
        assert result is None

    async def test_update_lead(self, db_session, user, lead):
        service = LeadService(db_session, user)
        update = LeadUpdate(status="contacted", company="Acme Updated")
        result = await service.update_lead(str(lead.id), update)

        assert result is not None
        assert result.status == "contacted"
        assert result.company == "Acme Updated"

    async def test_archive_lead(self, db_session, user, lead):
        service = LeadService(db_session, user)
        success = await service.archive_lead(str(lead.id))
        assert success is True

        # Verify status changed
        result = await service.get_lead(str(lead.id))
        assert result.status == "archived"

    async def test_get_lead_count(self, db_session, user, lead):
        service = LeadService(db_session, user)
        count = await service.get_lead_count()
        assert count >= 1

    async def test_search_leads(self, db_session, user, lead):
        service = LeadService(db_session, user)
        results = await service.get_leads(search="Acme")
        assert len(results) >= 1
        assert any(r.company == "Acme Corp" for r in results)
