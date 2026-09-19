from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.db.models.answer import Answer
from app.db.models.question import Question
from app.db.models.user import User


router = APIRouter(
    prefix="/api/v1/questions",
    tags=["Answers"],
)


@router.get("/{question_id}/answer")
def get_question_answer(
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

    # Make sure the question belongs to a document
    # owned by the authenticated user.
    if question.document.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this question",
        )

    answer = db.scalar(
        select(Answer).where(
            Answer.question_id == question_id
        )
    )

    if answer is None:
        raise HTTPException(
            status_code=404,
            detail="Answer not found",
        )

    return {
        "question_id": answer.question_id,
        "answer": answer.answer_label,
        "confidence": answer.confidence,
        "review_required": answer.review_required,
        "source_document_id": answer.source_document_id,
    }