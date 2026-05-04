import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EventInvitation(Base):
    __tablename__ = "event_invitations"
    __table_args__ = (
        CheckConstraint(
            "rsvp_status IN ('pending', 'accepted', 'rejected')",
            name="check_event_invitation_status",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id"), primary_key=True
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.event_id"), primary_key=True
    )
    rsvp_status: Mapped[str] = mapped_column(String(50))
    ics_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
