import re


ANSWER_PATTERNS = [
    re.compile(
        r"^\s*(?:Question\s*|Q\s*)?(\d+)\s*[\.\):-]\s*([A-Da-d])\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:Question\s*|Q\s*)?(\d+)\s*[-:]\s*([A-Da-d])\s*$",
        re.IGNORECASE,
    ),
]


def normalize_answer_text(text: str) -> str:
    """
    Normalize common OCR punctuation variations.
    """
    return (
        text.replace("—", "-")
        .replace("–", "-")
        .replace("−", "-")
    )


def normalize_question_number(value: str) -> str:
    """
    Extract only the numeric part of a question number.

    Examples:
        '1.'          -> '1'
        '2)'          -> '2'
        'Question 3.' -> '3'
        'Q4.'         -> '4'
    """
    match = re.search(r"\d+", str(value))

    if not match:
        return ""

    return match.group(0)


def parse_answer_key(text: str) -> dict[str, str]:
    """
    Parse answer-key text into:

        {
            "1": "A",
            "2": "C",
            "3": "B"
        }

    Supported formats include:

        1. A
        2. C
        3. B

        1) A
        2) C

        1-A
        2-C

        Question 1. A
        Question 2. C

        Q3. B
        Q4. D
    """

    answers: dict[str, str] = {}

    text = normalize_answer_text(text)

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        for pattern in ANSWER_PATTERNS:
            match = pattern.match(line)

            if not match:
                continue

            question_number = normalize_question_number(
                match.group(1)
            )

            answer = match.group(2).upper()

            if question_number:
                answers[question_number] = answer

            break

    return answers


def associate_answers(
    questions,
    parsed_answers: dict[str, str],
    source_document_id: int,
) -> list[dict]:
    """
    Associate parsed answer-key entries with extracted questions.

    Questions that do not have a matching answer are marked
    review_required=True.
    """

    results = []

    for question in questions:
        question_number = normalize_question_number(
            question.question_number
        )

        answer = parsed_answers.get(question_number)

        if answer is None:
            results.append(
                {
                    "question_id": question.id,
                    "source_document_id": source_document_id,
                    "answer_label": "",
                    "confidence": 0.0,
                    "review_required": True,
                }
            )

            continue

        results.append(
            {
                "question_id": question.id,
                "source_document_id": source_document_id,
                "answer_label": answer,
                "confidence": 1.0,
                "review_required": False,
            }
        )

    return results