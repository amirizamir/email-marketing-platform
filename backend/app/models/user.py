from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.contact import Contact
    from app.models.list import ContactList
    from app.models.smtp import SMTPAccount
    from app.models.template import EmailTemplate


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    smtp_accounts: Mapped[list["SMTPAccount"]] = relationship(back_populates="user")
    contact_lists: Mapped[list["ContactList"]] = relationship(back_populates="user")
    contacts: Mapped[list["Contact"]] = relationship(back_populates="user")
    templates: Mapped[list["EmailTemplate"]] = relationship(back_populates="user")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="user")
