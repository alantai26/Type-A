import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import event_invitations as invitations_repo
from app.repositories import events as events_repo
from app.repositories import friendships as friendships_repo


def create_invitations(
    db: Session,
    *,
    event_id: uuid.UUID,
    creator_id: uuid.UUID,
    user_ids: list[uuid.UUID],
) -> list:
    event = events_repo.get(db, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    if event.creator_id != creator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can invite",
        )

    user_ids = [uid for uid in user_ids if uid != creator_id]

    if user_ids:
        friend_rows = friendships_repo.list_friends_for_user(db, creator_id)
        friend_ids = {row.user_id for row in friend_rows}
        non_friends = [uid for uid in user_ids if uid not in friend_ids]
        if non_friends:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Not friends with: {non_friends}",
            )

    return invitations_repo.bulk_insert_invitations(
        db, event_id=event_id, user_ids=user_ids
    )


def update_my_rsvp(
    db: Session,
    *,
    event_id: uuid.UUID,
    user_id: uuid.UUID,
    rsvp_status: str,
):
    row = invitations_repo.update_rsvp(
        db, user_id=user_id, event_id=event_id, rsvp_status=rsvp_status
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No invitation to this event",
        )
    return row


def list_my_incoming(db: Session, *, user_id: uuid.UUID) -> list[dict]:
    return invitations_repo.list_incoming_for_user(db, user_id=user_id)
