import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.models.place_ratings import PlaceRating
from app.models.places import Place


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


def list_by_user(db: Session, user_id: uuid.UUID) -> list:
    inner = (
        select(PlaceRating)
        .where(PlaceRating.user_id == user_id)
        .order_by(PlaceRating.place_id, PlaceRating.created_at.desc())
        .distinct(PlaceRating.place_id)
        .subquery()
    )
    latest = aliased(PlaceRating, inner)
    return (
        db.query(
            latest.rating_id,
            latest.user_id,
            latest.place_id,
            latest.rating,
            latest.created_at,
            Place.name.label("place_name"),
            Place.category,
        )
        .join(Place, latest.place_id == Place.place_id)
        .order_by(latest.rating.desc())
        .all()
    )


def get_latest_for_user_place(
    db: Session, user_id: uuid.UUID, place_id: uuid.UUID
) -> PlaceRating | None:
    return db.scalars(
        select(PlaceRating)
        .where(PlaceRating.user_id == user_id, PlaceRating.place_id == place_id)
        .order_by(PlaceRating.created_at.desc())
    ).first()
