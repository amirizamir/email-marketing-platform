from app.schemas.auth import Token, UserCreate, UserOut, UserLogin
from app.schemas.campaign import (
    CampaignCreate,
    CampaignOut,
    CampaignSchedule,
    CampaignStats,
    CampaignUpdate,
)
from app.schemas.contact import ContactOut, ContactsUploadResult
from app.schemas.list import ContactListCreate, ContactListOut
from app.schemas.smtp import SMTPAccountCreate, SMTPAccountOut, SMTPTestRequest, SMTPTestExisting
from app.schemas.template import TemplateCreate, TemplateOut, TemplateUpdate

__all__ = [
    "Token",
    "UserCreate",
    "UserOut",
    "UserLogin",
    "SMTPAccountCreate",
    "SMTPAccountOut",
    "SMTPTestRequest",
    "SMTPTestExisting",
    "ContactListCreate",
    "ContactListOut",
    "ContactOut",
    "ContactsUploadResult",
    "TemplateCreate",
    "TemplateOut",
    "TemplateUpdate",
    "CampaignCreate",
    "CampaignOut",
    "CampaignSchedule",
    "CampaignStats",
    "CampaignUpdate",
]
