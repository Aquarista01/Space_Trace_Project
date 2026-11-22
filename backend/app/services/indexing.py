from sqlalchemy.orm import Session
from app.models.space import Space
from app.services.ai import embedder

SPACE_MATCH_THRESHOLD = 0.75


def find_or_create_space(db: Session, user_id, embedding) -> Space:
    candidates = db.query(Space).filter(Space.user_id == user_id).all()

    best_match = None
    best_score = 0.0
    for candidate in candidates:
        if candidate.canonical_embedding is None:
            continue
        score = embedder.cosine_similarity(embedding, embedder.from_bytes(candidate.canonical_embedding))
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_match and best_score >= SPACE_MATCH_THRESHOLD:
        return best_match

    new_space = Space(
        user_id=user_id,
        canonical_embedding=embedder.to_bytes(embedding),
    )
    db.add(new_space)
    db.flush()
    return new_space