import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.saved_places import SavedPlace
from app.models.users import User
from app.models.places import Place
from app.models.outings import Outing


def feed_saves(
    db: Session, *, friend_ids: list[uuid.UUID], before: datetime | None, limit: int
) -> list:
    query = (
        db.query(
            User.user_id.label("actor_id"),
            User.display_name,
            Place.place_id,
            Place.name.label("place_name"),
            SavedPlace.created_at,
        )
        .join(SavedPlace, SavedPlace.user_id == User.user_id)
        .join(Place, SavedPlace.place_id == Place.place_id)
        .filter(SavedPlace.user_id.in_(friend_ids))
    )
    if before is not None:
        query = query.filter(SavedPlace.created_at < before)
    return query.order_by(SavedPlace.created_at.desc()).limit(limit).all()

def feed_outings(
    db: Session, *, friend_ids: list[uuid.UUID], before: datetime | None, limit: int
) -> list:
    query = (
        db.query(
            User.user_id.label("actor_id"),
            User.display_name,
            Outing.outing_id,
            Outing.title,
            Outing.final_rating,
            Outing.completed_at("created_at"),
        )
        .join(User, Outing.creator_id == User.user_id)
        .filter(
            Outing.creator_id.in_(friend_ids),
            Outing.status == "completed",
            Outing.final_rating.is_not(None),
        )
    )
    if before is not None:
        query = query.filter(Outing.completed_at < before)
    return query.order_by(Outing.completed_at.desc()).limit(limit).all()


def feed_ratings(
    db: Session,
    *,
    friend_ids: list[uuid.UUID],
    before: datetime | None,
    limit: int,
) -> list:
    sql = """
        SELECT * FROM (
            SELECT DISTINCT ON (pr.user_id, pr.place_id)
                u.user_id   AS actor_id,
                u.display_name,
                p.place_id,
                p.name  AS place_name,
                pr.rating,
                pr.created_at
            FROM place_ratings pr
            JOIN users u ON pr.user_id = u.user_id
            JOIN places p ON pr.place_id = p.place_id
            WHERE pr.user_id = ANY(:friend_ids)
        """
    if before is not None:
        sql += " AND pr.created_at < :before"
    sql += """
            ORDER BY pr.user_id, pr.place_id, pr.created_at DESC
        ) latest
        ORDER BY created_at DESC
        LIMIT: limit
    """
    params = {"friend_ids": friend_ids, "limit": limit}

    if before is not None:
        params["before"] = before
    
    return db.execute(text(sql), params).all()