import uuid                                                                                                                      
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
                                                                                                                                          
                                                                                                                                          
class AttributionOutput(Base):                                                                                                                     
    __tablename__ = "attribution_outputs"

    attribution_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"))
    place_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("places.place_id"))
    attributed_effect: Mapped[float] = mapped_column()
    confidence_lower: Mapped[float] = mapped_column()
    confidence_upper: Mapped[float] = mapped_column()
    model_version: Mapped[str] = mapped_column(String(50))
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
