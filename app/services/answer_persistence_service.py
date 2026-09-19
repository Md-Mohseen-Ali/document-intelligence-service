from sqlalchemy.orm import Session

from app.db.models.answer import Answer


def save_answers(
    db: Session,
    associations: list[dict],
) -> list[Answer]:
    saved_answers = []

    for item in associations:
        answer = Answer(
            question_id=item["question_id"],
            source_document_id=item["source_document_id"],
            answer_label=item["answer_label"],
            confidence=item["confidence"],
            review_required=item["review_required"],
        )

        db.add(answer)
        saved_answers.append(answer)

    db.flush()

    return saved_answers
