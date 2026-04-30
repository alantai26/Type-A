import os
import uuid

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.users import User

SUPABASE_URL = os.environ["SUPABASE_URL"]
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"

_jwks_client = PyJWKClient(JWKS_URL, cache_keys=True, lifespan=600)


def _validate_token(token: str) -> dict:
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            signing_key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )


def _provision_user(db: Session, sub: str, email: str) -> User:
    user_id = uuid.UUID(sub)
    user = db.get(User, user_id)
    if user is None:
        user = User(
            user_id=user_id,
            email=email,
            display_name=email.split("@")[0],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def require_auth(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )
    token = authorization.removeprefix("Bearer ").strip()
    payload = _validate_token(token)
    sub = payload.get("sub")
    email = payload.get("email")
    if not sub or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT missing sub or email claim",
        )
    return _provision_user(db, sub, email)
