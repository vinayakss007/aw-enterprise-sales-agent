from datetime import datetime
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.models.campaign import Campaign, CampaignAssignment, CampaignStep
from app.db.models.lead import Lead
from app.db.models.user import User
from app.schemas.campaign import (
    CampaignCreate,
    CampaignResponse,
    CampaignUpdate,
)


class CampaignService:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.tenant_id = user.tenant_id

    async def get_campaigns(
        self, 
        skip: int = 0, 
        limit: int = 50
    ) -> list[CampaignResponse]:
        """
        Get paginated list of campaigns
        """
        query = self.db.query(Campaign).filter(Campaign.tenant_id == self.tenant_id)

        campaigns = query.offset(skip).limit(limit).all()

        results = []
        for campaign in campaigns:
            # Calculate metrics
            active_count = self.db.query(CampaignAssignment).filter(
                and_(
                    CampaignAssignment.campaign_id == campaign.id,
                    CampaignAssignment.status == 'active'
                )
            ).count()
            
            completed_count = self.db.query(CampaignAssignment).filter(
                and_(
                    CampaignAssignment.campaign_id == campaign.id,
                    CampaignAssignment.status == 'completed'
                )
            ).count()

            # Get steps
            steps = self.db.query(CampaignStep).filter(
                CampaignStep.campaign_id == campaign.id
            ).order_by(CampaignStep.order).all()

            results.append(CampaignResponse(
                id=campaign.id,
                name=campaign.name,
                description=campaign.description,
                status=campaign.status,
                steps=[{
                    'order': step.order,
                    'type': step.type,
                    'title': step.title,
                    'content': step.content,
                    'delay_days': step.delay_days,
                    'subject': step.subject
                } for step in steps],
                created_at=campaign.created_at,
                updated_at=campaign.updated_at,
                active_leads=active_count,
                completed_leads=completed_count
            ))

        return results

    async def create_campaign(self, campaign_in: CampaignCreate) -> CampaignResponse:
        """
        Create a new campaign
        """
        campaign = Campaign(
            tenant_id=self.tenant_id,
            name=campaign_in.name,
            description=campaign_in.description,
            status='draft',  # Start as draft
            created_by=self.user.id
        )
        
        self.db.add(campaign)
        self.db.flush()  # Get ID before creating steps
        
        # Create campaign steps
        for step_in in campaign_in.steps:
            step = CampaignStep(
                campaign_id=campaign.id,
                order=step_in.order,
                type=step_in.type,
                title=step_in.title,
                content=step_in.content,
                delay_days=step_in.delay_days,
                subject=step_in.subject
            )
            self.db.add(step)
        
        self.db.commit()
        self.db.refresh(campaign)
        
        # Return with steps
        steps = self.db.query(CampaignStep).filter(
            CampaignStep.campaign_id == campaign.id
        ).order_by(CampaignStep.order).all()

        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            status=campaign.status,
            steps=[{
                'order': step.order,
                'type': step.type,
                'title': step.title,
                'content': step.content,
                'delay_days': step.delay_days,
                'subject': step.subject
            } for step in steps],
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            active_leads=0,
            completed_leads=0
        )

    async def get_campaign(self, campaign_id: str) -> CampaignResponse | None:
        """
        Get a specific campaign by ID
        """
        campaign = self.db.query(Campaign).filter(
            and_(
                Campaign.id == campaign_id,
                Campaign.tenant_id == self.tenant_id
            )
        ).first()
        
        if not campaign:
            return None

        # Get steps
        steps = self.db.query(CampaignStep).filter(
            CampaignStep.campaign_id == campaign_id
        ).order_by(CampaignStep.order).all()

        # Calculate metrics
        active_count = self.db.query(CampaignAssignment).filter(
            and_(
                CampaignAssignment.campaign_id == campaign_id,
                CampaignAssignment.status == 'active'
            )
        ).count()
        
        completed_count = self.db.query(CampaignAssignment).filter(
            and_(
                CampaignAssignment.campaign_id == campaign_id,
                CampaignAssignment.status == 'completed'
            )
        ).count()

        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            status=campaign.status,
            steps=[{
                'order': step.order,
                'type': step.type,
                'title': step.title,
                'content': step.content,
                'delay_days': step.delay_days,
                'subject': step.subject
            } for step in steps],
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            active_leads=active_count,
            completed_leads=completed_count
        )

    async def update_campaign(self, campaign_id: str, campaign_in: CampaignUpdate) -> CampaignResponse | None:
        """
        Update campaign information
        """
        campaign = self.db.query(Campaign).filter(
            and_(
                Campaign.id == campaign_id,
                Campaign.tenant_id == self.tenant_id
            )
        ).first()
        
        if not campaign:
            return None

        # Update allowed fields
        update_data = campaign_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)

        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(campaign)

        # Return updated campaign with steps
        steps = self.db.query(CampaignStep).filter(
            CampaignStep.campaign_id == campaign_id
        ).order_by(CampaignStep.order).all()

        active_count = self.db.query(CampaignAssignment).filter(
            and_(
                CampaignAssignment.campaign_id == campaign_id,
                CampaignAssignment.status == 'active'
            )
        ).count()
        
        completed_count = self.db.query(CampaignAssignment).filter(
            and_(
                CampaignAssignment.campaign_id == campaign_id,
                CampaignAssignment.status == 'completed'
            )
        ).count()

        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            status=campaign.status,
            steps=[{
                'order': step.order,
                'type': step.type,
                'title': step.title,
                'content': step.content,
                'delay_days': step.delay_days,
                'subject': step.subject
            } for step in steps],
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            active_leads=active_count,
            completed_leads=completed_count
        )

    async def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign (soft delete by setting status to 'deleted')
        """
        campaign = self.db.query(Campaign).filter(
            and_(
                Campaign.id == campaign_id,
                Campaign.tenant_id == self.tenant_id
            )
        ).first()
        
        if not campaign:
            return False

        campaign.status = 'deleted'
        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def activate_campaign(self, campaign_id: str) -> bool:
        """
        Activate a campaign
        """
        campaign = self.db.query(Campaign).filter(
            and_(
                Campaign.id == campaign_id,
                Campaign.tenant_id == self.tenant_id
            )
        ).first()
        
        if not campaign:
            return False

        campaign.status = 'active'
        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def deactivate_campaign(self, campaign_id: str) -> bool:
        """
        Deactivate a campaign
        """
        campaign = self.db.query(Campaign).filter(
            and_(
                Campaign.id == campaign_id,
                Campaign.tenant_id == self.tenant_id
            )
        ).first()
        
        if not campaign:
            return False

        campaign.status = 'paused'
        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def add_leads_to_campaign(self, campaign_id: str, lead_ids: list[str]) -> dict[str, Any]:
        """
        Add leads to a campaign
        """
        campaign = self.db.query(Campaign).filter(
            and_(
                Campaign.id == campaign_id,
                Campaign.tenant_id == self.tenant_id
            )
        ).first()
        
        if not campaign:
            raise ValueError("Campaign not found or not accessible")

        # Verify leads belong to the same tenant
        leads = self.db.query(Lead).filter(
            and_(
                Lead.id.in_(lead_ids),
                Lead.tenant_id == self.tenant_id
            )
        ).all()

        # Determine when the first step should fire. If the campaign has a
        # leading step with ``delay_days`` set, honour it so newly added
        # leads don't get pinged immediately when the operator wants a wait.
        first_step = (
            self.db.query(CampaignStep)
            .filter(CampaignStep.campaign_id == campaign_id)
            .order_by(CampaignStep.order)
            .first()
        )
        from datetime import timedelta
        delay_days = (first_step.delay_days or 0) if first_step else 0
        next_action_date = datetime.utcnow() + timedelta(days=delay_days)

        added_count = 0
        for lead in leads:
            # Check if lead is already in campaign
            existing = self.db.query(CampaignAssignment).filter(
                and_(
                    CampaignAssignment.campaign_id == campaign_id,
                    CampaignAssignment.lead_id == lead.id
                )
            ).first()
            
            if not existing:
                assignment = CampaignAssignment(
                    campaign_id=campaign_id,
                    lead_id=lead.id,
                    status='pending',  # Will be activated when campaign is active
                    next_action_date=next_action_date
                )
                self.db.add(assignment)
                added_count += 1

        self.db.commit()
        
        return {
            "added_leads": added_count,
            "total_requested": len(lead_ids),
            "campaign_id": campaign_id
        }