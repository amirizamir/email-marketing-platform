from datetime import datetime

from pydantic import BaseModel, Field

from app.models.campaign import CampaignStatus


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    template_id: int
    sender_id: int
    list_id: int


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class CampaignOut(BaseModel):
    id: int
    name: str
    template_id: int
    sender_id: int
    list_id: int
    status: CampaignStatus
    scheduled_at: datetime | None
    total_recipients: int
    sent_count: int
    failed_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignSchedule(BaseModel):
    scheduled_at: datetime


class CampaignStats(BaseModel):
    sent: int
    failed: int
    pending: int
