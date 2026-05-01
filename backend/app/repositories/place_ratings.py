import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.models.place_ratings import PlaceRating


def create(
    db: Session,
    *,
    user_id: uuid.UUID,
    place_id: uuid.UUID,
    rating: float,
) -> PlaceRating:
    place_rating = PlaceRating(
        user_id=user_id,
        place_id=place_id,
        rating=rating,
    )
    db.add(place_rating)
    db.commit()
    db.refresh(place_rating)
    return place_rating


def list_by_user(db: Session, user_id: uuid.UUID) -> list[PlaceRating]:
    inner = (
        select(PlaceRating)
        .where(PlaceRating.user_id == user_id)
        .order_by(PlaceRating.place_id, PlaceRating.created_at.desc())
        .distinct(PlaceRating.place_id)
        .subquery()
    )
    latest = aliased(PlaceRating, inner)
    return list(db.scalars(select(latest).order_by(latest.rating.desc())).all())
