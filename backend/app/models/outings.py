import uuid                                                                                                                           
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
                                                                                                                                          
                                                                                                                                          
class Outing(Base):                                                                                                                     
    __tablename__ = "outings"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'confirmed', 'completed', 'cancelled')", name="check_outing_status"),
    )

    outing_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)                                               
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id")) 
    status: Mapped[str] = mapped_column(String(50))
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    final_rating: Mapped[float | None] = mapped_column()
    derived_score: Mapped[float | None] = mapped_column()
