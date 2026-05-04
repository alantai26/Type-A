import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.users import User
from app.schemas.event_invitations import (
    EventInvitationCreate,
    EventInvitationOut,
    EventInvitationRSVP,
    IncomingEventInvitationOut,
)
from app.services import event_invitations as invitations_service

router = APIRouter(tags=["event_invitations"])


@router.post(
    "/events/{event_id}/invitations",
    response_model=list[EventInvitationOut],
)
def create_event_invitations(
    event_id: uuid.UUID,
    body: EventInvitationCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list:
    return invitations_service.create_invitations(
        db,
        event_id=event_id,
        creator_id=current_user.user_id,
        user_ids=body.user_ids,
    )


@router.patch(
    "/events/{event_id}/invitations/me",
    response_model=EventInvitationOut,
)
def rsvp_event_invitation(
    event_id: uuid.UUID,
    body: EventInvitationRSVP,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> EventInvitationOut:
    row = invitations_service.update_my_rsvp(
        db,
        event_id=event_id,
        user_id=current_user.user_id,
        rsvp_status=body.rsvp_status,
    )
    return EventInvitationOut(
        user_id=row.user_id,
        event_id=row.event_id,
        rsvp_status=row.rsvp_status,
        ics_sent_at=row.ics_sent_at,
        invitee_name=current_user.display_name,
    )


@router.get(
    "/me/event_invitations",
    response_model=list[IncomingEventInvitationOut],
)
def list_my_event_invitations(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list:
    return invitations_service.list_my_incoming(db, user_id=current_user.user_id)
