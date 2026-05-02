import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.friendships import Friendship
from app.repositories import friendships as friendships_repo


def request(
    db: Session,
    *,
    requestor_id: uuid.UUID,
    recipient_id: uuid.UUID,
) -> Friendship:
    if requestor_id == recipient_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot friend yourself",
        )

    friendship = friendships_repo.get(
        db, user_a_id=requestor_id, user_b_id=recipient_id
    )
    if friendship:
        return friendship

    reverse = friendships_repo.get(db, user_a_id=recipient_id, user_b_id=requestor_id)

    if reverse and reverse.status == "pending":
        reverse.status = "accepted"
        mirror = Friendship(
            user_a_id=requestor_id,
            user_b_id=recipient_id,
            status="accepted",
        )
        db.add(mirror)
        db.commit()
        db.refresh(mirror)
        return mirror

    return friendships_repo.create_pending(
        db, user_a_id=requestor_id, user_b_id=recipient_id
    )


def accept(
    db: Session,
    *,
    requestor_id: uuid.UUID,
    recipient_id: uuid.UUID,
) -> Friendship:

    pending = friendships_repo.get(db, user_a_id=requestor_id, user_b_id=recipient_id)

    if not pending:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Did not find pending request from this user",
        )

    if pending.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already accepted",
        )

    pending.status = "accepted"
    mirror = Friendship(
        user_a_id=recipient_id, user_b_id=requestor_id, status="accepted"
    )

    db.add(mirror)
    db.commit()
    db.refresh(mirror)
    return mirror


def reject(
    db: Session,
    *,
    requestor_id: uuid.UUID,
    recipient_id: uuid.UUID,
) -> None:

    pending = friendships_repo.get(db, user_a_id=requestor_id, user_b_id=recipient_id)

    if not pending:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Did not find pending request from this user",
        )

    if pending.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already accepted",
        )

    friendships_repo.delete_one(db, user_a_id=requestor_id, user_b_id=recipient_id)


def unfriend(
    db: Session,
    *,
    user_id: uuid.UUID,
    other_id: uuid.UUID,
) -> None:
    deleted = (
        db.query(Friendship)
        .filter(
            or_(
                and_(
                    Friendship.user_a_id == user_id,
                    Friendship.user_b_id == other_id,
                ),
                and_(
                    Friendship.user_a_id == other_id,
                    Friendship.user_b_id == user_id,
                ),
            )
        )
        .delete(synchronize_session=False)
    )

    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not friends with this user",
        )

    db.commit()
