import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.object import ObjectEntity
from app.models.observation import Observation
from app.models.source_media import SourceMedia
from app.models.space import Space
from app.schemas.objects import (
    LastSeenOut,
    ObjectListItemOut,
)
from app.services import storage
import logging
import time

logger = logging.getLogger("spacetrace.timing")

router = APIRouter(prefix="/objects", tags=["Objects"])


def _latest_observations_by_object(db: Session, user_id: uuid.UUID) -> dict[uuid.UUID, Observation]:
    stmt = (
        select(Observation)
        .where(Observation.user_id == user_id, Observation.object_id.isnot(None))
        .distinct(Observation.object_id)
        .order_by(
            Observation.object_id,
            func.coalesce(Observation.observed_at, Observation.created_at).desc(),
        )
    )
    rows = db.execute(stmt).scalars().all()
    return {row.object_id: row for row in rows}

def _build_last_seen_map(
    db: Session, latest_map: dict[uuid.UUID, Observation]
) -> dict[uuid.UUID, LastSeenOut]:
    media_ids = {obs.media_id for obs in latest_map.values()}
    media_rows = db.query(SourceMedia).filter(SourceMedia.id.in_(media_ids)).all() if media_ids else []
    media_keys = {m.id: m.minio_key for m in media_rows}

    space_ids = {obs.space_id for obs in latest_map.values() if obs.space_id}
    space_rows = db.query(Space).filter(Space.id.in_(space_ids)).all() if space_ids else []
    space_names = {s.id: s.name for s in space_rows}

    result = {}
    for object_id, obs in latest_map.items():
        key = media_keys.get(obs.media_id)
        if key is None:
            continue
        result[object_id] = LastSeenOut(
            observed_at=obs.observed_at,
            space_id=obs.space_id,
            space_name=space_names.get(obs.space_id),
            media_id=obs.media_id,
            image_url=storage.get_presigned_url(key),
            confidence=obs.confidence,
            bbox_x=obs.bbox_x,
            bbox_y=obs.bbox_y,
            bbox_w=obs.bbox_w,
            bbox_h=obs.bbox_h,
        )
    return result

@router.get("", response_model=list[ObjectListItemOut])
def list_objects(db: Session = Depends(get_db), user=Depends(get_current_user)):
    t0 = time.perf_counter()
    objects = (
        db.query(ObjectEntity)
        .filter_by(user_id=user.id)
        .order_by(ObjectEntity.created_at.desc())
        .all()
    )
    t1 = time.perf_counter()
    logger.info("list: DB query objects %.1fms (%d rows)", (t1 - t0) * 1000, len(objects))

    latest_map = _latest_observations_by_object(db, user.id)
    t2 = time.perf_counter()
    logger.info("list: latest observations %.1fms", (t2 - t1) * 1000)

    last_seen_map = _build_last_seen_map(db, latest_map)
    t3 = time.perf_counter()
    logger.info("list: presigned urls %.1fms", (t3 - t2) * 1000)

    return [
        ObjectListItemOut(
            id=obj.id,
            label=obj.label,
            display_name=obj.display_name,
            is_confirmed=obj.is_confirmed,
            last_seen=last_seen_map.get(obj.id),
        )
        for obj in objects
    ]