import uuid                                                                                                                           
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
                                                                                                                                          
                                                                                                                                          
class Event(Base):                                                                                                                     
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'confirmed', 'completed', 'cancelled')", name="check_event_status"),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)                                               
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id")) 
    place_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("places.place_id"))
    custom_location_name: Mapped[str | None] = mapped_column(String(255))  # For user-defined locations
    outing_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("outings.outing_id"))
    sequence_position: Mapped[int | None] = mapped_column()  # Position in outing sequence, if part of an outing
    status: Mapped[str] = mapped_column(String(50))
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    weight: Mapped[float | None] = mapped_column()  # Stop weight within an outing (0.0-1.0)
