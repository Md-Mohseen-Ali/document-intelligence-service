from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QuestionPage(Base):
    __tablename__ = "question_pages"

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        primary_key=True,
    )

    page_id: Mapped[int] = mapped_column(
        ForeignKey("document_pages.id"),
        primary_key=True,
    )
