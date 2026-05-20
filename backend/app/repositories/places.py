import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.saved_places import SavedPlace
from app.models.users import User

# earth_box() does a fast GiST bounding-box prefilter; earth_distance() is the
# exact great-circle distance in meters. Both come from the earthdistance ext.
# ILIKE on name is accelerated by the pg_trgm GIN index.
_SEARCH_SQL = text("""
    SELECT
        p.place_id,
        p.name,
        p.category,
        p.latitude,
        p.longitude,
        earth_distance(
            ll_to_earth(p.latitude, p.longitude),
            ll_to_earth(:lat, :lng)
        ) AS distance_m,
        (sp.user_id IS NOT NULL) AS is_saved
    FROM places p
    LEFT JOIN saved_places sp
        ON sp.place_id = p.place_id
        AND sp.user_id = :user_id
    WHERE p.name ILIKE :q
        AND earth_box(ll_to_earth(:lat, :lng), :radius_m)
            @> ll_to_earth(p.latitude, p.longitude)
        AND earth_distance(
                ll_to_earth(p.latitude, p.longitude),
                ll_to_earth(:lat, :lng)
            ) < :radius_m
    ORDER BY distance_m ASC
    LIMIT 50
""")

# Nearby-only mode: q omitted, all places within radius_m returned by distance.
_NEARBY_SQL = text("""
    SELECT
        p.place_id,
        p.name,
        p.category,
        p.latitude,
        p.longitude,
        earth_distance(
            ll_to_earth(p.latitude, p.longitude),
            ll_to_earth(:lat, :lng)
        ) AS distance_m,
        (sp.user_id IS NOT NULL) AS is_saved
    FROM places p
    LEFT JOIN saved_places sp
        ON sp.place_id = p.place_id
        AND sp.user_id = :user_id
    WHERE earth_box(ll_to_earth(:lat, :lng), :radius_m)
            @> ll_to_earth(p.latitude, p.longitude)
        AND earth_distance(
                ll_to_earth(p.latitude, p.longitude),
                ll_to_earth(:lat, :lng)
            ) < :radius_m
    ORDER BY distance_m ASC
    LIMIT 50
""")


def search_places(
    db: Session,
    *,
    q: str | None,
    lat: float,
    lng: float,
    radius_m: float,
    user_id: uuid.UUID,
) -> list[dict]:
    params: dict = {
        "lat": lat,
        "lng": lng,
        "radius_m": radius_m,
        "user_id": user_id,
    }
    if q is None:
        sql = _NEARBY_SQL
    else:
        sql = _SEARCH_SQL
        params["q"] = f"%{q}%"
    rows = db.execute(sql, params).mappings().all()
    return [dict(r) for r in rows]


def friends_ratings_for_place(
    db: Session,
    *,
    friend_ids: list[uuid.UUID],
    place_id: uuid.UUID,
) -> list:
    sql = text("""                                    
          SELECT DISTINCT ON (pr.user_id)                                          
              u.user_id,                 
              u.display_name,                                                        
              pr.rating,                                
              pr.created_at                                                          
          FROM place_ratings pr          
          JOIN users u ON pr.user_id = u.user_id                                     
          WHERE pr.user_id = ANY(:friend_ids)
            AND pr.place_id = :place_id                                              
          ORDER BY pr.user_id, pr.created_at DESC       
      """)
    return db.execute(sql, {"friend_ids": friend_ids, "place_id": place_id}).all()


def friends_saves_for_place(
    db: Session, *, friend_ids: list[uuid.UUID], place_id: uuid.UUID
) -> list:
    return (
        db.query(
            User.user_id,
            User.display_name,
            SavedPlace.created_at,
        )
        .join(SavedPlace, SavedPlace.user_id == User.user_id)
        .filter(SavedPlace.user_id.in_(friend_ids), SavedPlace.place_id == place_id)
        .all()
    )
