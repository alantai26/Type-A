import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.events import Event
from app.repositories import events as events_repo
from app.repositories import outings as outings_repo


def create(
    db: Session,
    *,
    creator_id: uuid.UUID,
    place_id: uuid.UUID | None = None,
    custom_location_name: str | None = None,
    outing_id: uuid.UUID | None = None,
    sequence_position: int | None = None,
    scheduled_for=None,  # datetime | None — keeping import light
    weight: float | None = None,
) -> Event:
    # If attaching to an outing, validate it before we create anything.
    outing = None
    if outing_id is not None:
        outing = outings_repo.get(db, outing_id)
        if outing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Outing not found",
            )
        if outing.creator_id != creator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your outing",
            )
        if outing.status == "confirmed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot add stops to a confirmed outing — unconfirm first",
            )

    event = events_repo.create(
        db,
        creator_id=creator_id,
        place_id=place_id,
        custom_location_name=custom_location_name,
        outing_id=outing_id,
        sequence_position=sequence_position,
        scheduled_for=scheduled_for,
        weight=weight,
    )

    if outing is not None:
        outings_repo.recalc_scheduled_for(db, outing)

    return event


## Helper Function
def _check_editable(thing) -> None:
    """Raise 409 if a confirmed event/outing is being mutated."""
    if thing.status == "confirmed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot edit a confirmed plan — unconfirm first",
        )


def update(
    db: Session,
    event: Event,
    **fields,
) -> Event:

    _check_editable(event)

    parent_outing = None
    if event.outing_id is not None:
        parent_outing = outings_repo.get(db, event.outing_id)
        _check_editable(parent_outing)

    event = events_repo.update(db, event, **fields)

    if "scheduled_for" in fields and parent_outing is not None:
        outings_repo.recalc_scheduled_for(db, parent_outing)
    return event


def delete(db: Session, event: Event) -> None:
    _check_editable(event)

    parent_outing = None
    if event.outing_id is not None:
        parent_outing = outings_repo.get(db, event.outing_id)
        _check_editable(parent_outing)

    events_repo.delete(db, event)

    if parent_outing is not None:
        outings_repo.recalc_scheduled_for(db, parent_outing)


def confirm(db: Session, event: Event) -> Event:
    if event.outing_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="In-outing events are confirmed via the parent outing",
        )
    if event.scheduled_for is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="scheduled_for is required to confirm",
        )
    if event.place_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="place_id is required to confirm",
        )
    return events_repo.set_status(db, event, "confirmed")


def unconfirm(db: Session, event: Event) -> Event:
    if event.outing_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="In-outing events are unconfirmed via the parent outing",
        )
    if event.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event is not currently confirmed",
        )
    return events_repo.set_status(db, event, "planning_in_progress")


def cancel(db: Session, event: Event) -> Event:
    if event.outing_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="In-outing events are cancelled via the parent outing",
        )
    if event.status in ("cancelled", "completed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel an event that is already {event.status}",
        )
    return events_repo.set_status(db, event, "cancelled")
