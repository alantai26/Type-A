import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing import Literal
from app.schemas.events import EventOut


class EventInvitationCreate(BaseModel):
    user_ids: list[uuid.UUID]


class EventInvitationRSVP(BaseModel):
    rsvp_status: Literal["pending", "accepted", "rejected"]


class EventInvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    event_id: uuid.UUID
    rsvp_status: Literal["pending", "accepted", "rejected"]
    ics_sent_at: datetime | None
    invitee_name: str


class IncomingEventInvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event: EventOut
    creator_id: uuid.UUID
    creator_display_name: str
    rsvp_status: Literal["pending", "accepted", "rejected"]
    created_at: datetime
