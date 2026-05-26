from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class CampaignStatus(str, Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    completed = "completed"
    deleted = "deleted"

class CampaignStepType(str, Enum):
    email = "email"
    call = "call"
    task = "task"
    linkedin = "linkedin"

class CampaignStep(BaseModel):
    order: int
    type: CampaignStepType
    title: str
    content: str
    delay_days: int
    subject: str | None = None

class CampaignBase(BaseModel):
    name: str
    description: str | None = None

class CampaignCreate(CampaignBase):
    steps: list[CampaignStep]

class CampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: CampaignStatus | None = None

class CampaignResponse(CampaignBase):
    id: str
    status: CampaignStatus
    steps: list[CampaignStep]
    created_at: datetime
    updated_at: datetime
    active_leads: int
    completed_leads: int

    class Config:
        from_attributes = True