import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OutingInvitation(Base):
    __tablename__ = "outing_invitations"
    __table_args__ = (
        CheckConstraint(
            "rsvp_status IN ('pending', 'accepted', 'rejected')",
            name="check_outing_invitation_status",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id"), primary_key=True
    )
    outing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("outings.outing_id"), primary_key=True
    )
    rsvp_status: Mapped[str] = mapped_column(String(50))
    ics_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
