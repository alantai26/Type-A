from sqlalchemy.orm import Session

from app.models.users import User


def update_user(
    db: Session, user: User, *, display_name: str | None = None, bio: str | None = None
) -> User:
    if display_name is not None:
        user.display_name = display_name
    if bio is not None:
        user.bio = bio
    db.commit()
    db.refresh(user)
    return user
