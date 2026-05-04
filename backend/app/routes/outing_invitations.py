import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.users import User
from app.schemas.outing_invitations import (
    IncomingOutingInvitationOut,
    OutingInvitationCreate,
    OutingInvitationOut,
    OutingInvitationRSVP,
)
from app.services import outing_invitations as invitations_service

router = APIRouter(tags=["outing_invitations"])


@router.post(
    "/outings/{outing_id}/invitations",
    response_model=list[OutingInvitationOut],
)
def create_outing_invitations(
    outing_id: uuid.UUID,
    body: OutingInvitationCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list:
    return invitations_service.create_invitations(
        db,
        outing_id=outing_id,
        creator_id=current_user.user_id,
        user_ids=body.user_ids,
    )


@router.patch(
    "/outings/{outing_id}/invitations/me",
    response_model=OutingInvitationOut,
)
def rsvp_outing_invitation(
    outing_id: uuid.UUID,
    body: OutingInvitationRSVP,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> OutingInvitationOut:
    row = invitations_service.update_my_rsvp(
        db,
        outing_id=outing_id,
        user_id=current_user.user_id,
        rsvp_status=body.rsvp_status,
    )
    return OutingInvitationOut(
        user_id=row.user_id,
        outing_id=row.outing_id,
        rsvp_status=row.rsvp_status,
        ics_sent_at=row.ics_sent_at,
        invitee_name=current_user.display_name,
    )


@router.get(
    "/me/outing_invitations",
    response_model=list[IncomingOutingInvitationOut],
)
def list_my_outing_invitations(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list:
    return invitations_service.list_my_incoming(db, user_id=current_user.user_id)
