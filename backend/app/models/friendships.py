import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected')", name="check_status"
        ),
    )

    user_a_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id"), primary_key=True
    )
    user_b_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
