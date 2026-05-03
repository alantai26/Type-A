import uuid

from sqlalchemy.orm import Session

from datetime import datetime
from app.repositories import friendships as friendships_repo
from app.repositories import feed as feed_repo
from app.schemas.feed import FeedResponse, FeedRatingOut, FeedSaveOut, FeedOutingOut


def get_feed(
    db: Session,
    *,
    me: uuid.UUID,
    before: datetime | None,
    limit: int,
) -> FeedResponse:
    friends = friendships_repo.list_friends_for_user(db, user_id=me)
    friend_ids = [friend.user_id for friend in friends]

    if not friend_ids:
        return FeedResponse(items=[], next_cursor=None)

    saves = feed_repo.feed_saves(db, friend_ids=friend_ids, before=before, limit=limit)
    outings = feed_repo.feed_outings(
        db, friend_ids=friend_ids, before=before, limit=limit
    )
    ratings = feed_repo.feed_ratings(
        db, friend_ids=friend_ids, before=before, limit=limit
    )

    items = []
    for row in saves:
        items.append(FeedSaveOut(type="save", **row._mapping))

    for outing in outings:
        items.append(FeedOutingOut(type="outing", **outing._mapping))

    for rating in ratings:
        items.append(FeedRatingOut(type="rating", **rating._mapping))

    items.sort(key=lambda x: x.created_at, reverse=True)
    items = items[:limit]

    next_cursor = items[-1].created_at if len(items) == limit else None
    return FeedResponse(items=items, next_cursor=next_cursor)
