from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.db.models import User
from app.schemas.document import (
    DocumentResponse,
    DocumentStatusResponse,
)
from app.services.document_service import (
    create_document,
    get_user_document,
)
from app.services.processing_service import create_processing_job
from app.services.storage_service import save_upload
from app.worker.tasks import process_document


router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        storage_key = save_upload(file)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    document = create_document(
        db=db,
        user=current_user,
        original_filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        storage_key=storage_key,
    )

    job = create_processing_job(
        db=db,
        document_id=document.id,
    )

    task = process_document.delay(job.id)

    job.celery_task_id = task.id
    db.commit()

    return document


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
)
def get_document_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = get_user_document(
        db,
        current_user,
        document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document