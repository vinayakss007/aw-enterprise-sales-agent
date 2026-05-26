"""Campaign schemas."""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


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
    delay_days: int = 0
    subject: Optional[str] = None


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[CampaignStep]


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None


class CampaignResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    steps: List[CampaignStep]
    created_at: datetime
    updated_at: datetime
    active_leads: int = 0
    completed_leads: int = 0

    class Config:
        from_attributes = True
