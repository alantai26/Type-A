import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Place(Base):
    __tablename__ = "places"

    place_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()
    category: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(String(255))
    google_place_id: Mapped[str | None] = mapped_column(String(255), unique=True)
