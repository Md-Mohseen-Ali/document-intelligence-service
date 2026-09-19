from sqlalchemy.orm import Session

from app.db.models import ProcessingJob


def create_processing_job(
    db: Session,
    document_id: int,
) -> ProcessingJob:
    job = ProcessingJob(
        document_id=document_id,
        status="QUEUED",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job
