import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    running = "running"
    paused = "paused"
    completed = "completed"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_id: Mapped[int] = mapped_column(ForeignKey("email_templates.id", ondelete="RESTRICT"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("smtp_accounts.id", ondelete="RESTRICT"), index=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("contact_lists.id", ondelete="RESTRICT"), index=True)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status"),
        nullable=False,
        default=CampaignStatus.draft,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_recipients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="campaigns")
    template: Mapped["EmailTemplate"] = relationship(back_populates="campaigns")
    sender: Mapped["SMTPAccount"] = relationship(back_populates="campaigns")
    contact_list: Mapped["ContactList"] = relationship(back_populates="campaigns")
    email_jobs: Mapped[list["EmailJob"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="id",
    )


from typing import TYPE_CHECKING  # noqa: E402

if TYPE_CHECKING:
    from app.models.email_job import EmailJob
    from app.models.list import ContactList
    from app.models.smtp import SMTPAccount
    from app.models.template import EmailTemplate
    from app.models.user import User
