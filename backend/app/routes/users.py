from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.schemas.users import UserOut, UserUpdate
from app.models.users import User
from app.repositories.users import update_user

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(require_auth)) -> User:
    return current_user


@router.patch("/me", response_model=UserOut)
def patch_me(
    body: UserUpdate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> User:
    return update_user(db, current_user, display_name=body.display_name, bio=body.bio)
