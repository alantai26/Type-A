import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.places import Place
from app.models.users import User
from app.repositories import places as places_repo
from app.repositories import saved_places as saved_repo
from app.schemas.places import (
    FriendRatingOut,
    FriendSaveOut,
    PlaceOut,
    PlacePredictionOut,
)
from app.services import places as places_service

router = APIRouter(tags=["places"])


@router.get("/places", response_model=list[PlaceOut])
def search_places(
    q: str | None = Query(default=None, min_length=1),
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: float = Query(50000, gt=0, le=100000),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list[dict]:
    return places_repo.search_places(
        db,
        q=q,
        lat=lat,
        lng=lng,
        radius_m=radius_m,
        user_id=current_user.user_id,
    )


@router.get("/saved_places", response_model=list[PlaceOut])
def list_saved_places(
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list[dict]:
    return saved_repo.list_saved(db, user_id=current_user.user_id, lat=lat, lng=lng)


@router.post("/saved_places/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def save_place(
    place_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> None:
    if db.get(Place, place_id) is None:
        raise HTTPException(status_code=404, detail="Place not found")
    saved_repo.save(db, user_id=current_user.user_id, place_id=place_id)


@router.delete("/saved_places/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave_place(
    place_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> None:
    saved_repo.unsave(db, user_id=current_user.user_id, place_id=place_id)


@router.get("/places/{place_id}/predict", response_model=PlacePredictionOut)
def predict_place(
    place_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> PlacePredictionOut:
    if db.get(Place, place_id) is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return PlacePredictionOut(score=7.5, model_version="stub-v0")


@router.get(
    "/places/{place_id}/friends_activity",
    response_model=list[FriendRatingOut | FriendSaveOut],
)
def get_friends_activity(
    place_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list[FriendRatingOut | FriendSaveOut]:
    if db.get(Place, place_id) is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return places_service.get_friends_activity_for_place(
        db, me=current_user.user_id, place_id=place_id
    )
