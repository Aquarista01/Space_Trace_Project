

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.index_job import IndexJob
from app.models.source_media import SourceMedia


router = APIRouter(prefix="/photos", tags=["Photos"])

@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(SourceMedia).filter_by(user_id=user.id)

    last_sync = (
        db.query(func.max(IndexJob.created_at))
        .filter_by(user_id=user.id)
        .scalar()
    )

    return {
        "connected": bool(user.google_refresh_token_enc),
        "imported": q.count(),
        "indexed": q.filter(
            SourceMedia.index_status == "done"
        ).count(),
        "last_sync": last_sync,
    }