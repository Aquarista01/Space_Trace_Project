

from fastapi import APIRouter,Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.diff_item import DiffItem
from app.models.diff_result import DiffResult
from app.models.index_job import IndexJob
from app.models.object import ObjectEntity
from app.models.picker_session import PickerSession
from app.models.source_media import SourceMedia
from app.models.space import Space
from app.services import storage
from fastapi import APIRouter, Depends
from app.services import  storage

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
    
    
@router.delete("/data", status_code=204)
def delete_my_data(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    diff_ids = [
        d.id
        for d in db.query(DiffResult).filter_by(user_id=user.id)
    ]

    if diff_ids:
        db.query(DiffItem).filter(
            DiffItem.diff_id.in_(diff_ids)
        ).delete(synchronize_session=False)

        db.query(DiffResult).filter_by(
            user_id=user.id
        ).delete()

    for media in db.query(SourceMedia).filter_by(user_id=user.id):
        try:
            storage.delete_object(media.minio_key)
        except Exception:
            pass

    db.query(SourceMedia).filter_by(user_id=user.id).delete()
    db.query(IndexJob).filter_by(user_id=user.id).delete()
    db.query(PickerSession).filter_by(user_id=user.id).delete()
    db.query(ObjectEntity).filter_by(user_id=user.id).delete()
    db.query(Space).filter_by(user_id=user.id).delete()

    db.commit()