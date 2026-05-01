import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
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


class EventWeight(BaseModel):
    event_id: uuid.UUID
    weight: float = Field(ge=0, le=10)


class OutingRateRequest(BaseModel):
    event_weights: list[EventWeight]
    final_rating: float = Field(ge=0, le=10)
