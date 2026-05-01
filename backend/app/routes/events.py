import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.events import Event
from app.models.users import User
from app.repositories import events as events_repo
from app.schemas.events import EventCreate, EventOut, EventUpdate
from app.services import events as events_service

router = APIRouter(tags=["events"])


def _require_event(db: Session, event_id: uuid.UUID, current_user: User) -> Event:
    event = events_repo.get(db, event_id)
    if event is None or event.creator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


@router.post("/events", response_model=EventOut)
def create_event(
    body: EventCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Event:
    return events_service.create(
        db,
        creator_id=current_user.user_id,
        **body.model_dump(),
    )


@router.get("/events/{event_id}", response_model=EventOut)
def get_event(
    event_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Event:
    return _require_event(db, event_id, current_user)


@router.patch("/events/{event_id}", response_model=EventOut)
def update_event(
    event_id: uuid.UUID,
    body: EventUpdate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Event:
    event = _require_event(db, event_id, current_user)
    return events_service.update(db, event, **body.model_dump(exclude_unset=True))


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> None:
    event = _require_event(db, event_id, current_user)
    events_service.delete(db, event)


@router.post("/events/{event_id}/confirm", response_model=EventOut)
def confirm_event(
    event_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Event:
    event = _require_event(db, event_id, current_user)
    return events_service.confirm(db, event)


@router.post("/events/{event_id}/unconfirm", response_model=EventOut)
def unconfirm_event(
    event_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Event:
    event = _require_event(db, event_id, current_user)
    return events_service.unconfirm(db, event)


@router.post("/events/{event_id}/cancel", response_model=EventOut)
def cancel_event(
    event_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Event:
    event = _require_event(db, event_id, current_user)
    return events_service.cancel(db, event)


@router.post("/events/{event_id}/promote_to_outing", response_model=None)
def promote_event_to_outing(
    event_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Event:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Promote endpoint not yet implemented",
    )
