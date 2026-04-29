import uuid                                                                                                                           
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
                                                                                                                                          
                                                                                                                                          
class Comparison(Base):                                                                                                                     
    __tablename__ = "comparisons"
    __table_args__ = (
        CheckConstraint("item_type IN ('place', 'outing')", name="check_item_type"),
    )


    comparison_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"))
    item_a_id: Mapped[uuid.UUID] = mapped_column()
    item_b_id: Mapped[uuid.UUID] = mapped_column()
    item_type: Mapped[str] = mapped_column(String(50))
    winner_id: Mapped[uuid.UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)                                                                                          
    )        
