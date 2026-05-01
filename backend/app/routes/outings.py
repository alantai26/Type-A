import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.outings import Outing
from app.models.users import User
from app.repositories import outings as outings_repo
from app.schemas.outings import OutingCreate, OutingOut, OutingUpdate, OutingRateRequest
from app.services import outings as outings_service

router = APIRouter(tags=["outings"])


def _require_outing(db: Session, outing_id: uuid.UUID, current_user: User) -> Outing:
    outing = outings_repo.get(db, outing_id)
    if outing is None or outing.creator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outing not found",
        )
    return outing


@router.post("/outings", response_model=OutingOut)
def create_outing(
    body: OutingCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Outing:
    return outings_service.create(
        db,
        creator_id=current_user.user_id,
        **body.model_dump(),
    )


@router.get("/me/outings", response_model=list[OutingOut])
def list_my_outings(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> list[Outing]:
    return outings_repo.list_by_creator(db, current_user.user_id)


@router.get("/outings/{outing_id}", response_model=OutingOut)
def get_outing(
    outing_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Outing:
    return _require_outing(db, outing_id, current_user)


@router.patch("/outings/{outing_id}", response_model=OutingOut)
def update_outing(
    outing_id: uuid.UUID,
    body: OutingUpdate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Outing:
    outing = _require_outing(db, outing_id, current_user)
    return outings_service.update(db, outing, **body.model_dump(exclude_unset=True))


@router.delete("/outings/{outing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_outing(
    outing_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> None:
    outing = _require_outing(db, outing_id, current_user)
    outings_service.delete(db, outing)


@router.post("/outings/{outing_id}/confirm", response_model=OutingOut)
def confirm_outing(
    outing_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Outing:
    outing = _require_outing(db, outing_id, current_user)
    return outings_service.confirm(db, outing)


@router.post("/outings/{outing_id}/unconfirm", response_model=OutingOut)
def unconfirm_outing(
    outing_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Outing:
    outing = _require_outing(db, outing_id, current_user)
    return outings_service.unconfirm(db, outing)


@router.post("/outings/{outing_id}/cancel", response_model=OutingOut)
def cancel_outing(
    outing_id: uuid.UUID,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Outing:
    outing = _require_outing(db, outing_id, current_user)
    return outings_service.cancel(db, outing)


@router.post("/outings/{outing_id}/rate", response_model=OutingOut)
def rate_outing(
    outing_id: uuid.UUID,
    body: OutingRateRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Outing:
    outing = _require_outing(db, outing_id, current_user)
    return outings_service.rate(
        db, outing, final_rating=body.final_rating, weights=body.event_weights
    )
