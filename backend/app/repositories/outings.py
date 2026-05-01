import uuid
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.outings import Outing
from app.models.events import Event
from sqlalchemy import func, nulls_last


def create(
    db: Session,
    *,
    creator_id: uuid.UUID,
    title: str,
) -> Outing:
    outing = Outing(
        creator_id=creator_id,
        status="planning_in_progress",
        title=title,
    )
    db.add(outing)
    db.commit()
    db.refresh(outing)
    return outing


def get(db: Session, outing_id: uuid.UUID) -> Outing | None:
    return db.get(Outing, outing_id)


def list_by_creator(db: Session, creator_id: uuid.UUID) -> list[Outing]:
    return (
        db.query(Outing)
        .filter_by(creator_id=creator_id)
        .order_by(nulls_last(Outing.scheduled_for.desc()))
        .all()
    )


def update(db: Session, outing: Outing, **fields) -> Outing:
    for key, value in fields.items():
        setattr(outing, key, value)
    db.commit()
    db.refresh(outing)
    return outing


def delete(db: Session, outing: Outing) -> None:
    db.delete(outing)
    db.commit()


def set_status(db: Session, outing: Outing, status: str) -> Outing:
    outing.status = status
    db.commit()
    db.refresh(outing)
    return outing


def recalc_scheduled_for(db: Session, outing: Outing) -> Outing:
    new_value = (
        db.query(func.min(Event.scheduled_for))
        .filter_by(outing_id=outing.outing_id)
        .scalar()
    )
    outing.scheduled_for = new_value
    db.commit()
    db.refresh(outing)
    return outing
