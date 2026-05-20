import uuid

from sqlalchemy.orm import Session

from app.repositories import friendships as friendships_repo
from app.repositories import places as places_repo
from app.schemas.places import FriendRatingOut, FriendSaveOut


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
