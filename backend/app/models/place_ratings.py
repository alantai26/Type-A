import uuid                                                                                                                           
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
                                                                                                                                          
                                                                                                                                          
class PlaceRating(Base):                                                                                                                     
    __tablename__ = "place_ratings"

    rating_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)                                               
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id")) 
    place_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("places.place_id"))
    rating: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)                                                                                          
    )