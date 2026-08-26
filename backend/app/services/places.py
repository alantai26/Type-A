import uuid

from sqlalchemy.orm import Session

from app.ml.atomic_recommender import MODEL_VERSION, get_model, predict
from app.ml.data import normalize_category
from app.models.places import Place
from app.repositories import friendships as friendships_repo
from app.repositories import places as places_repo
from app.schemas.places import FriendRatingOut, FriendSaveOut, PlacePredictionOut


def get_friends_activity_for_place(
    db: Session,
    *,
    me: uuid.UUID,
    place_id: uuid.UUID,
) -> list[FriendRatingOut | FriendSaveOut]:
    friends = friendships_repo.list_friends_for_user(db, user_id=me)
    friend_ids = [f.user_id for f in friends]

    if not friend_ids:
        return []

    ratings = places_repo.friends_ratings_for_place(
        db, friend_ids=friend_ids, place_id=place_id
    )
    saves = places_repo.friends_saves_for_place(
        db, friend_ids=friend_ids, place_id=place_id
    )

    items: list[FriendRatingOut | FriendSaveOut] = []
    for row in ratings:
        items.append(FriendRatingOut(type="rating", **row._mapping))
    for row in saves:
        items.append(FriendSaveOut(type="save", **row._mapping))

    items.sort(key=lambda x: x.created_at, reverse=True)
    return items


def predict_score_for_place(*, user_id: uuid.UUID, place: Place) -> PlacePredictionOut:
    """Predicted rating for this user at this place, from the Atomic Recommender"""
    category = normalize_category(place.category)
    score = predict(get_model(), str(user_id), category)
    return PlacePredictionOut(score=round(score, 2), model_version=MODEL_VERSION)
