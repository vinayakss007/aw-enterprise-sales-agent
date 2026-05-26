from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db.models.lead import Lead
from app.db.models.user import User
from app.schemas.lead import LeadCreate, LeadResponse, LeadUpdate


class LeadService:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.tenant_id = user.tenant_id

    async def get_leads(
        self, 
        skip: int = 0, 
        limit: int = 50, 
        status: str | None = None, 
        search: str | None = None, 
        sort_by: str = "created_at", 
        sort_order: str = "desc"
    ) -> list[LeadResponse]:
        """
        Get paginated list of leads with filtering and sorting
        """
        query = self.db.query(Lead).filter(Lead.tenant_id == self.tenant_id)

        # Apply status filter
        if status:
            query = query.filter(Lead.status == status)

        # Apply search filter
        if search:
            search_filter = or_(
                Lead.name.ilike(f"%{search}%"),
                Lead.email.ilike(f"%{search}%"),
                Lead.company.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        # Apply sorting
        sort_column = getattr(Lead, sort_by)
        if sort_order == "desc":
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)

        # Execute query with pagination
        leads = query.offset(skip).limit(limit).all()

        return [self.lead_to_response(lead) for lead in leads]

    async def create_lead(self, lead_in: LeadCreate) -> LeadResponse:
        """
        Create a new lead
        """
        lead = Lead(
            tenant_id=self.tenant_id,
            user_id=self.user.id,
            **lead_in.model_dump(),
        )
        
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        
        return self.lead_to_response(lead)

    async def get_lead(self, lead_id: str) -> LeadResponse | None:
        """
        Get a specific lead by ID
        """
        lead = self.db.query(Lead).filter(
            and_(
                Lead.id == lead_id,
                Lead.tenant_id == self.tenant_id
            )
        ).first()
        
        if not lead:
            return None
            
        return self.lead_to_response(lead)

    async def update_lead(self, lead_id: str, lead_in: LeadUpdate) -> LeadResponse | None:
        """
        Update lead information
        """
        lead = self.db.query(Lead).filter(
            and_(
                Lead.id == lead_id,
                Lead.tenant_id == self.tenant_id
            )
        ).first()
        
        if not lead:
            return None

        # Update allowed fields
        update_data = lead_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)

        lead.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(lead)

        return self.lead_to_response(lead)

    async def archive_lead(self, lead_id: str) -> bool:
        """
        Archive a lead (soft delete)
        """
        lead = self.db.query(Lead).filter(
            and_(
                Lead.id == lead_id,
                Lead.tenant_id == self.tenant_id
            )
        ).first()
        
        if not lead:
            return False

        lead.status = "archived"
        lead.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def get_lead_activity(self, lead_id: str) -> list[dict]:
        """
        Get activity history for a lead
        """
        # This would typically query an activity table
        # For now, returning an empty list
        return []

    def lead_to_response(self, lead: Lead) -> LeadResponse:
        """
        Convert Lead model to LeadResponse schema
        """
        return LeadResponse(
            id=str(lead.id),
            email=lead.email,
            name=lead.name,
            company=lead.company,
            domain=lead.domain,
            title=lead.title,
            linkedin_url=lead.linkedin_url,
            phone=lead.phone,
            status=lead.status,
            source=lead.source,
            enriched_data=lead.enriched_data,
            crm_contact_id=lead.crm_contact_id,
            crm_account_id=lead.crm_account_id,
            tenant_id=str(lead.tenant_id),
            user_id=str(lead.user_id),
            created_at=lead.created_at,
            updated_at=lead.updated_at
        )