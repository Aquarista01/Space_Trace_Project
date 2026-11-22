import uuid

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.observation import Observation

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