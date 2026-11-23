import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.diff_item import DiffItem
from app.models.diff_result import DiffResult
from app.models.observation import Observation
from app.models.scene_state import SceneState
from app.models.source_media import SourceMedia
from app.models.space import Space
from app.schemas.space import (
    MergeSpacesIn,
    SceneOut,
    SpaceOut,
    SpaceUpdate,
)
from app.services import storage

router = APIRouter(prefix="/spaces", tags=["Spaces"])


def _change_counts(db: Session, user_id: uuid.UUID) -> dict[uuid.UUID, int]:
    latest_sub = (
        db.query(
            DiffResult.space_id,
            func.max(DiffResult.created_at).label("max_created_at"),
        )
        .filter(DiffResult.user_id == user_id)
        .group_by(DiffResult.space_id)
        .subquery()
    )

    latest_diffs = (
        db.query(DiffResult)
        .join(
            latest_sub,
            (DiffResult.space_id == latest_sub.c.space_id)
            & (DiffResult.created_at == latest_sub.c.max_created_at),
        )
        .all()
    )

    diff_ids = [d.id for d in latest_diffs]
    diff_to_space = {d.id: d.space_id for d in latest_diffs}

    if not diff_ids:
        return {}

    rows = (
        db.query(DiffItem.diff_id, func.count(DiffItem.id))
        .filter(
            DiffItem.diff_id.in_(diff_ids),
            DiffItem.change_type != "unchanged",
        )
        .group_by(DiffItem.diff_id)
        .all()
    )

    return {
        diff_to_space[diff_id]: count
        for diff_id, count in rows
    }


def _space_change_count(db: Session, space_id: uuid.UUID) -> int:
    latest_diff = (
        db.query(DiffResult)
        .filter(DiffResult.space_id == space_id)
        .order_by(DiffResult.created_at.desc())
        .first()
    )

    if latest_diff is None:
        return 0

    return (
        db.query(func.count(DiffItem.id))
        .filter(
            DiffItem.diff_id == latest_diff.id,
            DiffItem.change_type != "unchanged",
        )
        .scalar()
    ) or 0


@router.get("", response_model=list[SpaceOut])
def list_spaces(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    spaces = db.query(Space).filter_by(user_id=user.id).all()

    if not spaces:
        return []

    space_ids = [s.id for s in spaces]

    scene_counts = dict(
        db.query(SceneState.space_id, func.count(SceneState.id))
        .filter(SceneState.space_id.in_(space_ids))
        .group_by(SceneState.space_id)
        .all()
    )

    latest_sub = (
        db.query(
            SceneState.space_id,
            func.max(SceneState.taken_at).label("max_taken_at"),
        )
        .filter(SceneState.space_id.in_(space_ids))
        .group_by(SceneState.space_id)
        .subquery()
    )

    latest_scenes = (
        db.query(SceneState)
        .join(
            latest_sub,
            (SceneState.space_id == latest_sub.c.space_id)
            & (SceneState.taken_at == latest_sub.c.max_taken_at),
        )
        .all()
    )

    latest_by_space = {s.space_id: s for s in latest_scenes}

    media_ids = {s.media_id for s in latest_scenes}

    media_rows = (
        db.query(SourceMedia)
        .filter(SourceMedia.id.in_(media_ids))
        .all()
        if media_ids
        else []
    )

    media_keys = {m.id: m.minio_key for m in media_rows}

    change_counts = _change_counts(db, user.id)

    result = []

    for space in spaces:
        latest = latest_by_space.get(space.id)
        cover_url = None

        if latest:
            key = media_keys.get(latest.media_id)

            if key:
                cover_url = storage.get_presigned_url(key)

        result.append(
            SpaceOut(
                id=space.id,
                name=space.name,
                is_confirmed=space.is_confirmed,
                scene_count=scene_counts.get(space.id, 0),
                cover_url=cover_url,
                last_updated=latest.taken_at if latest else None,
                recent_changes=change_counts.get(space.id, 0),
            )
        )

    return result


@router.get("/{space_id}", response_model=SpaceOut)
def get_space(
    space_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    space = db.get(Space, space_id)

    if space is None or space.user_id != user.id:
        raise HTTPException(404, "Space not found")

    scene_count = (
        db.query(SceneState)
        .filter_by(space_id=space.id)
        .count()
    )

    latest = (
        db.query(SceneState)
        .filter_by(space_id=space.id)
        .order_by(SceneState.taken_at.desc())
        .first()
    )

    cover_url = None

    if latest:
        media = db.get(SourceMedia, latest.media_id)

        if media:
            cover_url = storage.get_presigned_url(media.minio_key)

    return SpaceOut(
        id=space.id,
        name=space.name,
        is_confirmed=space.is_confirmed,
        scene_count=scene_count,
        cover_url=cover_url,
        last_updated=latest.taken_at if latest else None,
        recent_changes=_space_change_count(db, space.id),
    )


@router.patch("/{space_id}", response_model=SpaceOut)
def update_space(
    space_id: uuid.UUID,
    payload: SpaceUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    space = db.get(Space, space_id)

    if space is None or space.user_id != user.id:
        raise HTTPException(404, "Space not found")

    if payload.name is not None:
        space.name = payload.name

    if payload.is_confirmed is not None:
        space.is_confirmed = payload.is_confirmed

    db.commit()
    db.refresh(space)

    return get_space(space_id, db, user)


@router.get("/{space_id}/scenes", response_model=list[SceneOut])
def list_scenes(
    space_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    space = db.get(Space, space_id)

    if space is None or space.user_id != user.id:
        raise HTTPException(404, "Space not found")

    scenes = (
        db.query(SceneState)
        .filter_by(space_id=space_id)
        .order_by(SceneState.taken_at.asc())
        .all()
    )

    if not scenes:
        return []

    scene_ids = [s.id for s in scenes]
    media_ids = {s.media_id for s in scenes}

    media_rows = (
        db.query(SourceMedia)
        .filter(SourceMedia.id.in_(media_ids))
        .all()
    )

    media_keys = {m.id: m.minio_key for m in media_rows}

    counts = dict(
        db.query(Observation.scene_id, func.count(Observation.id))
        .filter(Observation.scene_id.in_(scene_ids))
        .group_by(Observation.scene_id)
        .all()
    )

    result = []

    for scene in scenes:
        key = media_keys.get(scene.media_id)

        result.append(
            SceneOut(
                id=scene.id,
                taken_at=scene.taken_at,
                media_url=storage.get_presigned_url(key) if key else "",
                object_count=counts.get(scene.id, 0),
            )
        )

    return result


@router.post("/{space_id}/merge", response_model=SpaceOut)
def merge_spaces(
    space_id: uuid.UUID,
    payload: MergeSpacesIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if space_id == payload.source_id:
        raise HTTPException(400, "Cannot merge a space into itself")

    target = db.get(Space, space_id)
    source = db.get(Space, payload.source_id)

    if target is None or target.user_id != user.id:
        raise HTTPException(404, "Target space not found")

    if source is None or source.user_id != user.id:
        raise HTTPException(404, "Source space not found")

    db.query(SceneState).filter_by(space_id=source.id).update(
        {"space_id": target.id}
    )

    db.query(Observation).filter_by(space_id=source.id).update(
        {"space_id": target.id}
    )

    db.query(DiffResult).filter_by(space_id=source.id).update(
        {"space_id": target.id}
    )

    db.delete(source)
    db.commit()

    return get_space(space_id, db, user)