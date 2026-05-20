import uuid

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class PlaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    place_id: uuid.UUID
    name: str
    category: str
    latitude: float
    longitude: float
    distance_m: float | None = None
    is_saved: bool


class PlacePredictionOut(BaseModel):
    score: float
    model_version: str


class FriendRatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: Literal["rating"]
    user_id: uuid.UUID
    display_name: str
    rating: float
    created_at: datetime


class FriendSaveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: Literal["save"]
    user_id: uuid.UUID
    display_name: str
    created_at: datetime
