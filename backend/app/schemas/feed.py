import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from typing import Literal


class FeedRatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: Literal["rating"]
    actor_id: uuid.UUID
    display_name: str
    place_id: uuid.UUID
    place_name: str
    rating: float
    created_at: datetime


class FeedSaveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: Literal["save"]
    actor_id: uuid.UUID
    display_name: str
    place_id: uuid.UUID
    place_name: str
    created_at: datetime


class FeedOutingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: Literal["outing"]
    actor_id: uuid.UUID
    outing_id: uuid.UUID
    display_name: str
    title: str
    final_rating: float
    created_at: datetime


class FeedResponse(BaseModel):
    items: list[FeedRatingOut | FeedSaveOut | FeedOutingOut]
    next_cursor: datetime | None
