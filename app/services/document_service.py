from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, User


def create_document(
    db: Session,
    user: User,
    original_filename: str,
    content_type: str,
    storage_key: str,
) -> Document:
    document = Document(
        user_id=user.id,
        original_filename=original_filename,
        content_type=content_type,
        storage_key=storage_key,
        status="UPLOADED",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def get_user_document(
    db: Session,
    user: User,
    document_id: int,
) -> Document | None:
    return db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user.id,
        )
    )
