import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FriendRequestCreate(BaseModel):
    recipient_id: uuid.UUID


class FriendshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_a_id: uuid.UUID
    user_b_id: uuid.UUID
    status: str
    created_at: datetime


class FriendOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    display_name: str
    created_at: datetime
