from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ContactList(Base):
    __tablename__ = "contact_lists"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_contact_list_user_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="contact_lists")
    contacts: Mapped[list["Contact"]] = relationship(back_populates="contact_list", cascade="all, delete-orphan")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="contact_list")


from typing import TYPE_CHECKING  # noqa: E402

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.contact import Contact
    from app.models.user import User
