import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from app.schemas.events import EventOut


class OutingCreate(BaseModel):
    title: str


class OutingUpdate(BaseModel):
    title: str | None = None


class OutingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    outing_id: uuid.UUID
    creator_id: uuid.UUID
    title: str
    status: str
    scheduled_for: datetime | None
    completed_at: datetime | None
    final_rating: float | None
    derived_score: float | None
    events: list[EventOut]
