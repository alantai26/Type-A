import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing import Literal
from app.schemas.outings import OutingOut


class OutingInvitationCreate(BaseModel):
    user_ids: list[uuid.UUID]


class OutingInvitationRSVP(BaseModel):
    rsvp_status: Literal["pending", "accepted", "rejected"]


class OutingInvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    outing_id: uuid.UUID
    rsvp_status: Literal["pending", "accepted", "rejected"]
    ics_sent_at: datetime | None
    invitee_name: str


class IncomingOutingInvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    outing: OutingOut
    creator_id: uuid.UUID
    creator_display_name: str
    rsvp_status: Literal["pending", "accepted", "rejected"]
    created_at: datetime
