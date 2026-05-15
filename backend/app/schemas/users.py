import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    bio: str | None = None
    email: str
    display_name: str
    created_at: datetime


class UserUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = Field(default=None, max_length=160)
