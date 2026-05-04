import uuid

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.event_invitations import EventInvitation
from app.models.events import Event
from app.models.users import User


def bulk_insert_invitations(
    db: Session, *, event_id: uuid.UUID, user_ids: list[uuid.UUID]
) -> list:
    if not user_ids:
        return []

    rows = [
        {"user_id": uid, "event_id": event_id, "rsvp_status": "pending"}
        for uid in user_ids
    ]
    stmt = (
        insert(EventInvitation)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["user_id", "event_id"])
    )
    db.execute(stmt)
    db.commit()

    return (
        db.query(
            EventInvitation.user_id,
            EventInvitation.event_id,
            EventInvitation.rsvp_status,
            EventInvitation.ics_sent_at,
            User.display_name.label("invitee_name"),
        )
        .join(User, User.user_id == EventInvitation.user_id)
        .filter(
            EventInvitation.event_id == event_id,
            EventInvitation.user_id.in_(user_ids),
        )
        .all()
    )


def get_invitation(
    db: Session, *, user_id: uuid.UUID, event_id: uuid.UUID
) -> EventInvitation | None:
    return (
        db.query(EventInvitation).filter_by(user_id=user_id, event_id=event_id).first()
    )


def update_rsvp(
    db: Session,
    *,
    user_id: uuid.UUID,
    event_id: uuid.UUID,
    rsvp_status: str,
) -> EventInvitation | None:
    row = get_invitation(db, user_id=user_id, event_id=event_id)
    if row is None:
        return None
    row.rsvp_status = rsvp_status
    db.commit()
    db.refresh(row)
    return row


def list_incoming_for_user(db: Session, *, user_id: uuid.UUID) -> list[dict]:
    rows = (
        db.query(
            EventInvitation.rsvp_status,
            EventInvitation.created_at,
            Event,
            User.display_name.label("creator_display_name"),
        )
        .join(Event, Event.event_id == EventInvitation.event_id)
        .join(User, User.user_id == Event.creator_id)
        .filter(EventInvitation.user_id == user_id)
        .order_by(EventInvitation.created_at.desc())
        .all()
    )
    return [
        {
            "event": row.Event,
            "creator_id": row.Event.creator_id,
            "creator_display_name": row.creator_display_name,
            "rsvp_status": row.rsvp_status,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def insert_creator_self(
    db: Session, *, event_id: uuid.UUID, creator_id: uuid.UUID
) -> None:
    stmt = (
        insert(EventInvitation)
        .values(user_id=creator_id, event_id=event_id, rsvp_status="accepted")
        .on_conflict_do_nothing(index_elements=["user_id", "event_id"])
    )
    db.execute(stmt)
    db.commit()
