import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.place_ratings import PlaceRating
from app.models.users import User
from app.repositories import place_ratings as place_ratings_repo
from app.schemas.place_ratings import PlaceRatingCreate, PlaceRatingOut

router = APIRouter(tags=["place_ratings"])


@router.post("/place_ratings", response_model=PlaceRatingOut)
def create_place_rating(
    body: PlaceRatingCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> PlaceRating:
    return place_ratings_repo.create(
        db,
        user_id=current_user.user_id,
        place_id=body.place_id,
        rating=body.rating,
    )


@router.get("/me/place_ratings", response_model=list[PlaceRatingOut])
def list_my_place_ratings(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    return place_ratings_repo.list_by_user(db, current_user.user_id)


@router.get("/places/{place_id}/my_rating", response_model=PlaceRatingOut | None)
def get_my_rating_for_place(
    place_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> PlaceRating | None:
    return place_ratings_repo.get_latest_for_user_place(
        db, current_user.user_id, place_id
    )
