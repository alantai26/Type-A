import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.events import Event


class Outing(Base):
    __tablename__ = "outings"
    __table_args__ = (
        CheckConstraint(
            "status IN ('planning_in_progress', 'confirmed', 'completed', 'cancelled')",
            name="check_outing_status",
        ),
    )

    outing_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"))
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    final_rating: Mapped[float | None] = mapped_column()
    derived_score: Mapped[float | None] = mapped_column()

    events: Mapped[list["Event"]] = relationship(
        back_populates="outing",
        order_by="Event.sequence_position",
    )
