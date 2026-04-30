import uuid

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.saved_places import SavedPlace

_LIST_SQL = text("""
    SELECT
        p.place_id,
        p.name,
        p.latitude,
        p.longitude,
        earth_distance(
            ll_to_earth(p.latitude, p.longitude),
            ll_to_earth(:lat, :lng)
        ) AS distance_m,
        TRUE AS is_saved
    FROM saved_places sp
    JOIN places p ON p.place_id = sp.place_id
    WHERE sp.user_id = :user_id
    ORDER BY distance_m ASC
""")


def list_saved(
    db: Session, *, user_id: uuid.UUID, lat: float, lng: float
) -> list[dict]:
    rows = db.execute(
        _LIST_SQL, {"user_id": user_id, "lat": lat, "lng": lng}
    ).mappings().all()
    return [dict(r) for r in rows]


def save(db: Session, *, user_id: uuid.UUID, place_id: uuid.UUID) -> None:
    # ON CONFLICT DO NOTHING makes a re-save a no-op instead of a 500.
    stmt = (
        insert(SavedPlace)
        .values(user_id=user_id, place_id=place_id)
        .on_conflict_do_nothing(index_elements=["user_id", "place_id"])
    )
    db.execute(stmt)
    db.commit()


def unsave(db: Session, *, user_id: uuid.UUID, place_id: uuid.UUID) -> None:
    db.query(SavedPlace).filter_by(user_id=user_id, place_id=place_id).delete()
    db.commit()
