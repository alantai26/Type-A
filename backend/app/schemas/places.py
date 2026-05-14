import uuid

from pydantic import BaseModel, ConfigDict


class PlaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    place_id: uuid.UUID
    name: str
    latitude: float
    longitude: float
    distance_m: float | None = None
    is_saved: bool


class PlacePredictionOut(BaseModel):
    score: float
    model_version: str
