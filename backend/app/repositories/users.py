from sqlalchemy.orm import Session

from app.models.users import User


def update_user(db: Session, user: User, *, display_name: str | None = None) -> User:
    if display_name is not None:
        user.display_name = display_name
    db.commit()
    db.refresh(user)
    return user
