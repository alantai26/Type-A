import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.outings import Outing
from app.repositories import events as events_repo
from app.repositories import outing_invitations as outing_invitations_repo
from app.repositories import outings as outings_repo
from app.services.events import _check_editable
from app.schemas.outings import EventWeight

from datetime import datetime, UTC


def create(
    db: Session,
    *,
    creator_id: uuid.UUID,
    title: str,
) -> Outing:
    outing = outings_repo.create(db, creator_id=creator_id, title=title)
    outing_invitations_repo.insert_creator_self(
        db, outing_id=outing.outing_id, creator_id=creator_id
    )
    return outing


def update(
    db: Session,
    outing: Outing,
    **fields,
) -> Outing:
    _check_editable(outing)
    return outings_repo.update(db, outing, **fields)


def delete(db: Session, outing: Outing) -> None:
    _check_editable(outing)
    outings_repo.delete(db, outing)


def confirm(db: Session, outing: Outing) -> Outing:
    if outing.status == "confirmed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Outing is already confirmed",
        )

    events = events_repo.list_by_outing(db, outing.outing_id)

    if len(events) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least 2 events are required to confirm an outing",
        )

    for event in events:
        if event.scheduled_for is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Event {event.event_id} is missing scheduled_for",
            )
        if event.place_id is None and event.custom_location_name is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Event {event.event_id} needs a place or custom_location_name",
            )
    outings_repo.recalc_scheduled_for(db, outing)

    outings_repo.set_status(db, outing, "confirmed")
    for event in events:
        events_repo.set_status(db, event, "confirmed")

    return outing


def unconfirm(db: Session, outing: Outing) -> Outing:
    if outing.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Outing is not confirmed yet",
        )

    events = events_repo.list_by_outing(db, outing.outing_id)

    outings_repo.set_status(db, outing, "planning_in_progress")
    for event in events:
        events_repo.set_status(db, event, "planning_in_progress")

    return outing


def cancel(db: Session, outing: Outing) -> Outing:
    if outing.status in ("cancelled", "completed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel an outing that is already {outing.status}",
        )

    events = events_repo.list_by_outing(db, outing.outing_id)

    outings_repo.set_status(db, outing, "cancelled")
    for event in events:
        events_repo.set_status(db, event, "cancelled")

    return outing


def rate(
    db: Session, outing: Outing, *, final_rating: float, weights: list[EventWeight]
) -> Outing:
    if outing.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot rate an unconfirmed outing",
        )

    outing_event_ids = {e.event_id for e in outing.events}
    body_event_ids = {w.event_id for w in weights}

    if outing_event_ids != body_event_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="All events must have weights",
        )

    if abs(sum(w.weight for w in weights) - 1.0) > 0.001:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Event weights must sum to 1.0",
        )

    weights_by_id = {w.event_id: w.weight for w in weights}
    now = datetime.now(UTC)

    outing.final_rating = final_rating
    outing.status = "completed"
    outing.completed_at = now

    for event in outing.events:
        event.weight = weights_by_id[event.event_id]
        event.status = "completed"
        event.completed_at = now

    db.commit()
    db.refresh(outing)
    return outing
