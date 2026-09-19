from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.db.models import (
    Question,
    QuestionOption,
    QuestionPage,
    DocumentPage,
    Answer,
    User,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Questions"],
)


@router.get("/documents/{document_id}/questions")
def get_document_questions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    questions = db.scalars(
        select(Question)
        .where(Question.document_id == document_id)
        .order_by(Question.id)
    ).all()

    if questions:
        document = questions[0].document

        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this document",
            )

    result = []

    for question in questions:
        options = db.scalars(
            select(QuestionOption)
            .where(
                QuestionOption.question_id
                == question.id
            )
        ).all()

        page_links = db.scalars(
            select(QuestionPage)
            .where(
                QuestionPage.question_id
                == question.id
            )
        ).all()

        page_ids = [link.page_id for link in page_links]

        pages = []

        if page_ids:
            pages = db.scalars(
                select(DocumentPage).where(
                    DocumentPage.id.in_(page_ids)
                )
            ).all()

        answer = db.scalar(
            select(Answer).where(
                Answer.question_id == question.id
            )
        )

        result.append(
            {
                "id": question.id,
                "question_number": question.question_number,
                "question_text": question.question_text,
                "options": [
                    {
                        "label": option.option_label,
                        "text": option.option_text,
                    }
                    for option in options
                ],
                "answer": (
                    answer.answer_label
                    if answer
                    else None
                ),
                "answer_confidence": (
                    answer.confidence
                    if answer
                    else None
                ),
                "confidence": question.confidence,
                "review_required": question.review_required,
                "source_pages": [
                    page.page_number
                    for page in pages
                ],
            }
        )

    return {
        "document_id": document_id,
        "questions": result,
        "total": len(result),
    }


@router.get("/questions/{question_id}")
def get_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = db.scalar(
        select(Question).where(
            Question.id == question_id
        )
    )

    if question is None:
        raise HTTPException(
            status_code=404,
            detail="Question not found",
        )

    if question.document.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this question",
        )

    options = db.scalars(
        select(QuestionOption).where(
            QuestionOption.question_id
            == question.id
        )
    ).all()

    page_links = db.scalars(
        select(QuestionPage).where(
            QuestionPage.question_id
            == question.id
        )
    ).all()

    page_ids = [link.page_id for link in page_links]

    pages = []

    if page_ids:
        pages = db.scalars(
            select(DocumentPage).where(
                DocumentPage.id.in_(page_ids)
            )
        ).all()

    answer = db.scalar(
        select(Answer).where(
            Answer.question_id == question.id
        )
    )

    return {
        "id": question.id,
        "document_id": question.document_id,
        "question_number": question.question_number,
        "question_text": question.question_text,
        "options": [
            {
                "label": option.option_label,
                "text": option.option_text,
            }
            for option in options
        ],
        "answer": (
            answer.answer_label
            if answer
            else None
        ),
        "answer_confidence": (
            answer.confidence
            if answer
            else None
        ),
        "confidence": question.confidence,
        "review_required": question.review_required,
        "source_pages": [
            page.page_number
            for page in pages
        ],
    }
