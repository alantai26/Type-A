from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.auth import require_auth
from app.db import get_db
from app.models.users import User
from app.services import feed as feed_service
from app.schemas.feed import FeedResponse

router = APIRouter(tags=["feed"])


@router.get("/me/feed", response_model=FeedResponse)
def get_feed(
    before: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> FeedResponse:
    return feed_service.get_feed(
        db, me=current_user.user_id, before=before, limit=limit
    )
