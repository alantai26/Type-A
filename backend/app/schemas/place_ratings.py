import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlaceRatingCreate(BaseModel):
    place_id: uuid.UUID
    rating: float = Field(ge=0, le=10)


class PlaceRatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rating_id: uuid.UUID
    user_id: uuid.UUID
    place_id: uuid.UUID
    rating: float
    created_at: datetime
