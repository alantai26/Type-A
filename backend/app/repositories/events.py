import uuid
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.events import Event


def create(
    db: Session,
    *,
    creator_id: uuid.UUID,
    place_id: uuid.UUID | None = None,
    custom_location_name: str | None = None,
    outing_id: uuid.UUID | None = None,
    sequence_position: int | None = None,
    scheduled_for: datetime | None = None,
    weight: float | None = None,
) -> Event:
    event = Event(
        creator_id=creator_id,
        place_id=place_id,
        custom_location_name=custom_location_name,
        outing_id=outing_id,
        sequence_position=sequence_position,
        status="planning_in_progress",
        scheduled_for=scheduled_for,
        weight=weight,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get(db: Session, event_id: uuid.UUID) -> Event | None:
    return db.get(Event, event_id)


def list_by_outing(db: Session, outing_id: uuid.UUID) -> list[Event]:
    return (
        db.query(Event)
        .filter_by(outing_id=outing_id)
        .order_by(Event.sequence_position)
        .all()
    )


def update(db: Session, event: Event, **fields) -> Event:
    for key, value in fields.items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return event


def delete(db: Session, event: Event) -> None:
    db.delete(event)
    db.commit()


def set_status(db: Session, event: Event, status: str) -> Event:
    event.status = status
    db.commit()
    db.refresh(event)
    return event
