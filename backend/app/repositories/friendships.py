import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.models.friendships import Friendship
from app.models.users import User


def get(
    db: Session, *, user_a_id: uuid.UUID, user_b_id: uuid.UUID
) -> Friendship | None:
    return (
        db.query(Friendship).filter_by(user_a_id=user_a_id, user_b_id=user_b_id).first()
    )


def create_pending(
    db: Session, *, user_a_id: uuid.UUID, user_b_id: uuid.UUID
) -> Friendship:
    friendship = Friendship(
        user_a_id=user_a_id,
        user_b_id=user_b_id,
        status="pending",
    )
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    return friendship


def delete_one(db: Session, *, user_a_id: uuid.UUID, user_b_id: uuid.UUID) -> None:
    db.query(Friendship).filter_by(user_a_id=user_a_id, user_b_id=user_b_id).delete()
    db.commit()


def list_friends_for_user(db: Session, user_id: uuid.UUID) -> list:
    return (
        db.query(User.user_id, User.display_name, Friendship.created_at)
        .join(Friendship, Friendship.user_b_id == User.user_id)
        .filter(
            Friendship.user_a_id == user_id,
            Friendship.status == "accepted",
        )
        .all()
    )


def list_pending_for_user(db: Session, user_id: uuid.UUID) -> list:
    return (
        db.query(User.user_id, User.display_name, Friendship.created_at)
        .join(Friendship, Friendship.user_a_id == User.user_id)
        .filter(
            Friendship.user_b_id == user_id,
            Friendship.status == "pending",
        )
        .all()
    )
