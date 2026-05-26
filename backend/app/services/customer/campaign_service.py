"""Campaign management service."""
from typing import List, Optional, Dict, Any
from sqlalchemy import and_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.models.campaign import Campaign, CampaignStep as CampaignStepModel, CampaignAssignment
from app.db.models.lead import Lead
from app.db.models.user import User
from app.schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignStep as CampaignStepSchema,
)


class CampaignService:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.tenant_id = user.tenant_id

    async def get_campaigns(self, skip: int = 0, limit: int = 50) -> List[CampaignResponse]:
        """Get paginated list of campaigns."""
        campaigns = (
            self.db.query(Campaign)
            .filter(Campaign.tenant_id == self.tenant_id, Campaign.status != "deleted")
            .order_by(Campaign.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_response(c) for c in campaigns]

    async def create_campaign(self, campaign_in: CampaignCreate) -> CampaignResponse:
        """Create a new campaign with steps."""
        campaign = Campaign(
            tenant_id=self.tenant_id,
            name=campaign_in.name,
            description=campaign_in.description,
            status="draft",
            created_by=self.user.id,
        )
        self.db.add(campaign)
        self.db.flush()

        for step_in in campaign_in.steps:
            step = CampaignStepModel(
                campaign_id=campaign.id,
                order=step_in.order,
                type=step_in.type,
                title=step_in.title,
                content=step_in.content,
                delay_days=step_in.delay_days,
                subject=step_in.subject,
            )
            self.db.add(step)

        self.db.commit()
        self.db.refresh(campaign)
        return self._to_response(campaign)

    async def get_campaign(self, campaign_id: str) -> Optional[CampaignResponse]:
        """Get a specific campaign."""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.tenant_id == self.tenant_id,
        ).first()
        return self._to_response(campaign) if campaign else None

    async def update_campaign(self, campaign_id: str, campaign_in: CampaignUpdate) -> Optional[CampaignResponse]:
        """Update campaign information."""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.tenant_id == self.tenant_id,
        ).first()

        if not campaign:
            return None

        update_data = campaign_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)

        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(campaign)
        return self._to_response(campaign)

    async def delete_campaign(self, campaign_id: str) -> bool:
        """Soft delete a campaign."""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.tenant_id == self.tenant_id,
        ).first()

        if not campaign:
            return False

        campaign.status = "deleted"
        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def activate_campaign(self, campaign_id: str) -> bool:
        """Activate a campaign and schedule its assignments."""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.tenant_id == self.tenant_id,
        ).first()

        if not campaign:
            return False

        campaign.status = "active"
        campaign.updated_at = datetime.utcnow()

        # Activate pending assignments
        assignments = self.db.query(CampaignAssignment).filter(
            CampaignAssignment.campaign_id == campaign_id,
            CampaignAssignment.status == "pending",
        ).all()

        for assignment in assignments:
            assignment.status = "active"
            # Schedule first step
            first_step = (
                self.db.query(CampaignStepModel)
                .filter(CampaignStepModel.campaign_id == campaign_id)
                .order_by(CampaignStepModel.order)
                .first()
            )
            if first_step:
                assignment.next_action_date = datetime.utcnow() + timedelta(days=first_step.delay_days)

        self.db.commit()
        return True

    async def deactivate_campaign(self, campaign_id: str) -> bool:
        """Pause a campaign."""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.tenant_id == self.tenant_id,
        ).first()

        if not campaign:
            return False

        campaign.status = "paused"
        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def add_leads_to_campaign(self, campaign_id: str, lead_ids: List[str]) -> Dict[str, Any]:
        """Add leads to a campaign."""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.tenant_id == self.tenant_id,
        ).first()

        if not campaign:
            return {"error": "Campaign not found", "added_leads": 0}

        # Get valid leads
        leads = self.db.query(Lead).filter(
            Lead.id.in_(lead_ids),
            Lead.tenant_id == self.tenant_id,
        ).all()

        added_count = 0
        for lead in leads:
            existing = self.db.query(CampaignAssignment).filter(
                CampaignAssignment.campaign_id == campaign_id,
                CampaignAssignment.lead_id == lead.id,
            ).first()

            if not existing:
                status = "active" if campaign.status == "active" else "pending"
                assignment = CampaignAssignment(
                    campaign_id=campaign.id,
                    lead_id=lead.id,
                    status=status,
                    next_action_date=datetime.utcnow(),
                )
                self.db.add(assignment)
                added_count += 1

        self.db.commit()
        return {
            "added_leads": added_count,
            "total_requested": len(lead_ids),
            "campaign_id": str(campaign_id),
        }

    def _to_response(self, campaign: Campaign) -> CampaignResponse:
        steps = [
            CampaignStepSchema(
                order=s.order,
                type=s.type,
                title=s.title,
                content=s.content,
                delay_days=s.delay_days,
                subject=s.subject,
            )
            for s in campaign.steps
        ]

        active_count = self.db.query(CampaignAssignment).filter(
            CampaignAssignment.campaign_id == campaign.id,
            CampaignAssignment.status == "active",
        ).count()

        completed_count = self.db.query(CampaignAssignment).filter(
            CampaignAssignment.campaign_id == campaign.id,
            CampaignAssignment.status == "completed",
        ).count()

        return CampaignResponse(
            id=str(campaign.id),
            name=campaign.name,
            description=campaign.description,
            status=campaign.status,
            steps=steps,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            active_leads=active_count,
            completed_leads=completed_count,
        )
