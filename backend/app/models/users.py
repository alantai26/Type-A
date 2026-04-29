import uuid                                                                                                                           
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
                                                                                                                                          
                                                                                                                                          
class User(Base):                                                                                                                     
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    display_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(                                                                                           
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)                                                                                          
    )                  
