import uuid

from fastapi import APIRouter, Depends, HTTPException
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
from app.schemas.photos import  PickerSessionOut
from app.services import google_photos, indexing, storage
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.schemas.photos import  PickerSessionOut
from app.services import google_photos, indexing, media_ingest, storage
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
    
    
@router.post(
    "/picker-sessions",
    response_model=PickerSessionOut,
)
def create_session(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    access_token = google_photos.get_access_token(db, user.id)

    data = google_photos.create_picker_session(access_token)

    session = PickerSession(
        user_id=user.id,
        google_session_id=data["id"],
        picker_uri=data["pickerUri"],
        status="created",
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.get(
    "/picker-sessions/{session_id}",
    response_model=PickerSessionOut,
)
def poll_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = db.get(PickerSession, session_id)

    if session is None or session.user_id != user.id:
        raise HTTPException(404, "Session not found")

    access_token = google_photos.get_access_token(db, user.id)

    data = google_photos.get_picker_session(
        access_token,
        session.google_session_id,
    )

    if data.get("mediaItemsSet"):
        session.status = "picked"
        db.commit()

    return session  

def run_import(
    job_id: uuid.UUID,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    db_factory,
):
    db = db_factory()

    try:
        job = db.get(IndexJob, job_id)
        session = db.get(PickerSession, session_id)

        access_token = google_photos.get_access_token(db, user_id)

        items = google_photos.list_picked_media_items(
            access_token,
            session.google_session_id,
        )

        job.total = len(items)
        db.commit()

        for item in items:
            try:
                media_file = item["mediaFile"]

                content = google_photos.download_media_bytes(
                    access_token,
                    media_file["baseUrl"],
                )

                mime_type = media_file.get(
                    "mimeType",
                    "image/jpeg",
                )

                captured_at = media_ingest.parse_create_time(
                    item.get("createTime")
                )

                existing = (
                    db.query(SourceMedia)
                    .filter_by(
                        user_id=user_id,
                        google_item_id=item["id"],
                    )
                    .first()
                )

                if existing is not None:
                    media = existing
                else:
                    media, _ = media_ingest.save_media(
                        db,
                        user_id,
                        content,
                        mime_type,
                        captured_at=captured_at,
                        google_item_id=item["id"],
                    )

                try:
                    indexing.process_media(db, media)
                except Exception:
                    import traceback
                    traceback.print_exc()
                    media.index_status = "failed"

                job.processed += 1

            except Exception:
                job.failed += 1

            db.commit()

        session.status = "done"
        job.status = "done"
        db.commit()

    finally:
        db.close()