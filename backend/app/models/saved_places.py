import uuid                                                                                                                           
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
                                                                                                                                          
                                                                                                                                          
class SavedPlace(Base):                                                                                                                     
    __tablename__ = "saved_places"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"), primary_key=True)                                               
    place_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("places.place_id"), primary_key=True) 
    created_at: Mapped[datetime] = mapped_column(                                                                                           
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)                                                                                          
    )      
