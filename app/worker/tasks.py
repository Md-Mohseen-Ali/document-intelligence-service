from datetime import datetime, timezone

from sqlalchemy import create_engine, select, desc
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import (
    Document,
    DocumentPage,
    ProcessingJob,
    Question,
    QuestionOption,
    QuestionPage,
    Answer,
)
from app.services.pdf_service import extract_pdf_pages
from app.services.question_extraction_service import (
    extract_questions_from_text,
)
from app.services.answer_key_service import (
    parse_answer_key,
    associate_answers,
)
from app.worker.celery_app import celery_app


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def looks_like_answer_key(text: str) -> bool:
    """
    Determine whether the extracted document looks like an answer key.

    Example supported formats:

        1. A
        2. C
        3. B

        1-A
        2-C

        Question 1. A
        Q2. C

    We require at least two detected answers so that a normal
    question document is not accidentally classified as an
    answer key.
    """

    parsed_answers = parse_answer_key(text)

    if len(parsed_answers) < 2:
        return False

    non_empty_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not non_empty_lines:
        return False

    # Answer keys generally contain a high proportion of
    # short number -> option lines.
    answer_ratio = len(parsed_answers) / len(non_empty_lines)

    return answer_ratio >= 0.40


def find_latest_question_document(
    db,
    current_document: Document,
):
    """
    Find the most recent completed question document belonging
    to the same user.

    This provides a simple MVP relationship for a separately
    uploaded answer-key document.
    """

    return db.scalar(
        select(Document)
        .join(
            Question,
            Question.document_id == Document.id,
        )
        .where(
            Document.user_id == current_document.user_id,
            Document.id != current_document.id,
            Document.status == "COMPLETED",
        )
        .order_by(desc(Document.created_at))
        .limit(1)
    )


@celery_app.task(
    bind=True,
    name="process_document",
)
def process_document(
    self,
    processing_job_id: int,
):
    db = SessionLocal()

    try:
        # -------------------------------------------------
        # STEP 1: Find processing job
        # -------------------------------------------------

        job = db.scalar(
            select(ProcessingJob).where(
                ProcessingJob.id == processing_job_id
            )
        )

        if job is None:
            return {
                "status": "FAILED",
                "message": "Processing job not found",
            }

        # -------------------------------------------------
        # STEP 2: Find document
        # -------------------------------------------------

        document = db.scalar(
            select(Document).where(
                Document.id == job.document_id
            )
        )

        if document is None:
            job.status = "FAILED"
            job.error_message = "Document not found"
            db.commit()

            return {
                "status": "FAILED",
                "message": "Document not found",
            }

        # -------------------------------------------------
        # STEP 3: Mark processing
        # -------------------------------------------------

        job.status = "PROCESSING"
        job.started_at = datetime.now(timezone.utc)

        document.status = "PROCESSING"

        db.commit()

        # -------------------------------------------------
        # STEP 4: Extract pages
        # -------------------------------------------------

        extracted_pages = extract_pdf_pages(
            document.storage_key
        )

        # -------------------------------------------------
        # STEP 5: Replace previous page records
        # -------------------------------------------------

        existing_pages = db.scalars(
            select(DocumentPage).where(
                DocumentPage.document_id == document.id
            )
        ).all()

        for existing_page in existing_pages:
            db.delete(existing_page)

        db.flush()

        page_records = []

        for page_data in extracted_pages:
            page = DocumentPage(
                document_id=document.id,
                page_number=page_data["page_number"],
                extracted_text=page_data["extracted_text"],
                is_scanned=page_data["is_scanned"],
                ocr_confidence=page_data[
                    "ocr_confidence"
                ],
            )

            db.add(page)
            page_records.append(page)

        db.flush()

        # -------------------------------------------------
        # STEP 6: Build document-level text
        # -------------------------------------------------

        combined_parts = []

        for page in page_records:

            if not page.extracted_text:
                continue

            combined_parts.append(
                f"\n--- PAGE {page.page_number} ---\n"
            )

            combined_parts.append(
                page.extracted_text
            )

        combined_text = "\n".join(
            combined_parts
        )

        # -------------------------------------------------
        # STEP 7: Detect answer-key document
        # -------------------------------------------------

        is_answer_key = looks_like_answer_key(
            combined_text
        )

        if is_answer_key:

            parsed_answers = parse_answer_key(
                combined_text
            )

            question_document = (
                find_latest_question_document(
                    db,
                    document,
                )
            )

            if question_document is None:

                job.status = "COMPLETED"
                job.completed_at = datetime.now(
                    timezone.utc
                )

                document.status = "COMPLETED"

                db.commit()

                return {
                    "status": "COMPLETED",
                    "document_id": document.id,
                    "processing_job_id": job.id,
                    "pages_processed": len(
                        page_records
                    ),
                    "questions_extracted": 0,
                    "is_answer_key": True,
                    "answers_parsed": len(
                        parsed_answers
                    ),
                    "answers_associated": 0,
                    "message": (
                        "Answer key processed, "
                        "but no question document "
                        "was available for association."
                    ),
                }

            # ---------------------------------------------
            # Get questions from the related question doc
            # ---------------------------------------------

            questions = db.scalars(
                select(Question).where(
                    Question.document_id
                    == question_document.id
                )
            ).all()

            associations = associate_answers(
                questions=questions,
                parsed_answers=parsed_answers,
                source_document_id=document.id,
            )

            # ---------------------------------------------
            # Remove previous answers from this answer key
            # ---------------------------------------------

            existing_answers = db.scalars(
                select(Answer).where(
                    Answer.source_document_id
                    == document.id
                )
            ).all()

            for existing_answer in existing_answers:
                db.delete(existing_answer)

            db.flush()

            # ---------------------------------------------
            # Persist answers
            # ---------------------------------------------

            answers_associated = 0

            for item in associations:

                answer = Answer(
                    question_id=item["question_id"],
                    source_document_id=item[
                        "source_document_id"
                    ],
                    answer_label=item["answer_label"],
                    confidence=item["confidence"],
                    review_required=item[
                        "review_required"
                    ],
                )

                db.add(answer)

                if not item["review_required"]:
                    answers_associated += 1

            db.flush()

            # ---------------------------------------------
            # Complete answer-key processing
            # ---------------------------------------------

            job.status = "COMPLETED"

            job.completed_at = datetime.now(
                timezone.utc
            )

            document.status = "COMPLETED"

            db.commit()

            return {
                "status": "COMPLETED",
                "document_id": document.id,
                "processing_job_id": job.id,
                "pages_processed": len(
                    page_records
                ),
                "questions_extracted": 0,
                "is_answer_key": True,
                "answers_parsed": len(
                    parsed_answers
                ),
                "answers_associated": answers_associated,
                "question_document_id": (
                    question_document.id
                ),
            }

        # =================================================
        # NORMAL QUESTION DOCUMENT PROCESSING
        # =================================================

        # -------------------------------------------------
        # STEP 8: Remove previous questions
        # -------------------------------------------------

        existing_questions = db.scalars(
            select(Question).where(
                Question.document_id == document.id
            )
        ).all()

        for question in existing_questions:
            db.delete(question)

        db.flush()

        # -------------------------------------------------
        # STEP 9: Extract questions
        # -------------------------------------------------

        extracted_questions = (
            extract_questions_from_text(
                combined_text
            )
        )

        total_questions = 0

        # -------------------------------------------------
        # STEP 10: Persist questions
        # -------------------------------------------------

        for question_data in extracted_questions:

            question = Question(
                document_id=document.id,
                question_number=question_data[
                    "question_number"
                ],
                question_text=question_data[
                    "question_text"
                ],
                confidence=0.80,
                review_required=False,
            )

            db.add(question)
            db.flush()

            # ---------------------------------------------
            # Determine source pages
            # ---------------------------------------------

            question_number = (
                question_data["question_number"]
            )

            matching_pages = []

            for page in page_records:

                page_text = (
                    page.extracted_text or ""
                )

                question_marker_patterns = [
                    f"{question_number}.",
                    f"{question_number})",
                    f"Question {question_number}",
                    f"Q{question_number}",
                    f"Q. {question_number}",
                ]

                contains_question_marker = any(
                    marker.lower()
                    in page_text.lower()
                    for marker in question_marker_patterns
                )

                if contains_question_marker:
                    matching_pages.append(page)

            # ---------------------------------------------
            # Handle continuation pages
            # ---------------------------------------------

            continuation_marker = (
                f"Question {question_number}"
            ).lower()

            for page in page_records:

                page_text = (
                    page.extracted_text or ""
                ).lower()

                if (
                    continuation_marker
                    in page_text
                    and "continued"
                    in page_text
                ):
                    if page not in matching_pages:
                        matching_pages.append(page)

            # ---------------------------------------------
            # Fallback page association
            # ---------------------------------------------

            if not matching_pages:

                question_text = (
                    question_data[
                        "question_text"
                    ]
                    .strip()
                    .lower()
                )

                for page in page_records:

                    page_text = (
                        page.extracted_text or ""
                    ).lower()

                    if (
                        question_text
                        and question_text[:40]
                        in page_text
                    ):
                        matching_pages.append(
                            page
                        )

            # ---------------------------------------------
            # Persist question-page relationships
            # ---------------------------------------------

            for page in matching_pages:

                question_page = QuestionPage(
                    question_id=question.id,
                    page_id=page.id,
                )

                db.add(question_page)

            # ---------------------------------------------
            # Store options
            # ---------------------------------------------

            for option_data in question_data[
                "options"
            ]:

                option = QuestionOption(
                    question_id=question.id,
                    option_label=option_data[
                        "option_label"
                    ],
                    option_text=option_data[
                        "option_text"
                    ],
                )

                db.add(option)

            total_questions += 1

        db.flush()

        # -------------------------------------------------
        # STEP 11: Complete processing
        # -------------------------------------------------

        job.status = "COMPLETED"

        job.completed_at = datetime.now(
            timezone.utc
        )

        document.status = "COMPLETED"

        db.commit()

        return {
            "status": "COMPLETED",
            "document_id": document.id,
            "processing_job_id": job.id,
            "pages_processed": len(
                page_records
            ),
            "questions_extracted": total_questions,
            "is_answer_key": False,
        }

    except Exception as error:

        db.rollback()

        job = db.scalar(
            select(ProcessingJob).where(
                ProcessingJob.id
                == processing_job_id
            )
        )

        if job is not None:

            job.status = "FAILED"
            job.error_message = str(error)

            document = db.scalar(
                select(Document).where(
                    Document.id == job.document_id
                )
            )

            if document is not None:
                document.status = "FAILED"

            db.commit()

        raise

    finally:
        db.close()