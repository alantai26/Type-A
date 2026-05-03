import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.friendships import Friendship
from app.models.users import User
from app.repositories import friendships as friendships_repo
from app.services import friendships as friendships_service
from app.schemas.friendships import FriendOut, FriendRequestCreate, FriendshipOut

router = APIRouter(tags=["friendships"])


@router.post("/friends/requests", response_model=FriendshipOut)
def send_friend_request(
    body: FriendRequestCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Friendship:
    return friendships_service.request(
        db, requestor_id=current_user.user_id, recipient_id=body.recipient_id
    )


@router.post("/friends/requests/{user_id}/accept", response_model=FriendshipOut)
def accept_friend_request(
    user_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Friendship:
    return friendships_service.accept(
        db, requestor_id=user_id, recipient_id=current_user.user_id
    )


@router.post(
    "/friends/requests/{user_id}/reject", status_code=status.HTTP_204_NO_CONTENT
)
def reject_friend_request(
    user_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> None:
    return friendships_service.reject(
        db, requestor_id=user_id, recipient_id=current_user.user_id
    )


@router.delete("/me/friends/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfriend(
    user_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> None:
    return friendships_service.unfriend(
        db, user_id=current_user.user_id, other_id=user_id
    )


@router.get("/me/friends", response_model=list[FriendOut])
def list_my_friends(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list:
    return friendships_repo.list_friends_for_user(db, user_id=current_user.user_id)


@router.get("/me/friend_requests", response_model=list[FriendOut])
def list_pending_friend_requests(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list:
    return friendships_repo.list_pending_for_user(db, user_id=current_user.user_id)
