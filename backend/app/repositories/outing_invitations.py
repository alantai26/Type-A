import uuid

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.outing_invitations import OutingInvitation
from app.models.outings import Outing
from app.models.users import User


def bulk_insert_invitations(
    db: Session, *, outing_id: uuid.UUID, user_ids: list[uuid.UUID]
) -> list:
    if not user_ids:
        return []

    rows = [
        {"user_id": uid, "outing_id": outing_id, "rsvp_status": "pending"}
        for uid in user_ids
    ]
    stmt = (
        insert(OutingInvitation)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["user_id", "outing_id"])
    )
    db.execute(stmt)
    db.commit()

    return (
        db.query(
            OutingInvitation.user_id,
            OutingInvitation.outing_id,
            OutingInvitation.rsvp_status,
            OutingInvitation.ics_sent_at,
            User.display_name.label("invitee_name"),
        )
        .join(User, User.user_id == OutingInvitation.user_id)
        .filter(
            OutingInvitation.outing_id == outing_id,
            OutingInvitation.user_id.in_(user_ids),
        )
        .all()
    )


def get_invitation(
    db: Session, *, user_id: uuid.UUID, outing_id: uuid.UUID
) -> OutingInvitation | None:
    return (
        db.query(OutingInvitation)
        .filter_by(user_id=user_id, outing_id=outing_id)
        .first()
    )


def update_rsvp(
    db: Session,
    *,
    user_id: uuid.UUID,
    outing_id: uuid.UUID,
    rsvp_status: str,
) -> OutingInvitation | None:
    row = get_invitation(db, user_id=user_id, outing_id=outing_id)
    if row is None:
        return None
    row.rsvp_status = rsvp_status
    db.commit()
    db.refresh(row)
    return row


def list_incoming_for_user(db: Session, *, user_id: uuid.UUID) -> list[dict]:
    rows = (
        db.query(
            OutingInvitation.rsvp_status,
            OutingInvitation.created_at,
            Outing,
            User.display_name.label("creator_display_name"),
        )
        .join(Outing, Outing.outing_id == OutingInvitation.outing_id)
        .join(User, User.user_id == Outing.creator_id)
        .filter(OutingInvitation.user_id == user_id)
        .order_by(OutingInvitation.created_at.desc())
        .all()
    )
    return [
        {
            "outing": row.Outing,
            "creator_id": row.Outing.creator_id,
            "creator_display_name": row.creator_display_name,
            "rsvp_status": row.rsvp_status,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def insert_creator_self(
    db: Session, *, outing_id: uuid.UUID, creator_id: uuid.UUID
) -> None:
    stmt = (
        insert(OutingInvitation)
        .values(user_id=creator_id, outing_id=outing_id, rsvp_status="accepted")
        .on_conflict_do_nothing(index_elements=["user_id", "outing_id"])
    )
    db.execute(stmt)
    db.commit()
