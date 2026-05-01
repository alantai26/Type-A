import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    place_id: uuid.UUID | None = None
    custom_location_name: str | None = None
    sequence_position: int | None = None
    outing_id: uuid.UUID | None = None
    scheduled_for: datetime | None = None
    weight: float | None = None


class EventUpdate(BaseModel):
    place_id: uuid.UUID | None = None
    custom_location_name: str | None = None
    sequence_position: int | None = None
    scheduled_for: datetime | None = None
    weight: float | None = None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: uuid.UUID
    creator_id: uuid.UUID
    place_id: uuid.UUID | None
    custom_location_name: str | None
    outing_id: uuid.UUID | None
    sequence_position: int | None
    status: str
    scheduled_for: datetime | None
    completed_at: datetime | None
    weight: float | None
