import re


QUESTION_PATTERN = re.compile(
    r"(?im)^(?:"
    r"Question\s+(?:No\.?\s*)?(\d+)"
    r"|Q(?:uestion)?\.?\s*(\d+)"
    r"|(\d+)[.)]"
    r")"
    r"(?:\s*[-:.)]\s*|\s+)"
    r"(.*)$"
)


OPTION_PATTERN = re.compile(
    r"(?im)^\s*"
    r"(\([A-Za-z]\)|[A-Za-z][.)]|"
    r"\([ivxIVX]+\)|[ivxIVX][.)])"
    r"[ \t]+"
)


PAGE_MARKER_PATTERN = re.compile(
    r"(?im)^\s*---\s*PAGE\s+(\d+)\s*---\s*$"
)


QUESTION_WORDS = (
    "what",
    "why",
    "how",
    "which",
    "who",
    "where",
    "when",
    "explain",
    "describe",
    "define",
    "discuss",
    "identify",
    "compare",
    "write",
    "list",
    "give",
    "state",
    "calculate",
    "find",
    "implement",
    "design",
)


def looks_like_question(text: str) -> bool:
    text = text.strip()

    if not text:
        return False

    lowered = text.lower()

    if "?" in text:
        return True

    return lowered.startswith(QUESTION_WORDS)


def is_continuation(text: str) -> bool:
    lowered = text.strip().lower()

    continuation_markers = (
        "continued",
        "continuation",
        "contd",
        "cont.",
    )

    return any(
        marker in lowered
        for marker in continuation_markers
    )


def is_page_marker(text: str) -> bool:
    return bool(
        PAGE_MARKER_PATTERN.match(
            text.strip()
        )
    )


def clean_question_text(text: str) -> str:

    # -------------------------------------------------
    # Remove our internal page markers.
    #
    # Example:
    # --- PAGE 3 ---
    # -------------------------------------------------

    text = PAGE_MARKER_PATTERN.sub(
        "",
        text,
    )

    # -------------------------------------------------
    # Remove common page headers/footers.
    #
    # Examples:
    # Question Extraction Test — Page 2
    # Sample Paper - Page 3
    # Examination – Page 10
    # -------------------------------------------------

    text = re.sub(
        r"(?im)^\s*.*?\s+[—–-]\s*Page\s+\d+\s*$",
        "",
        text,
    )

    # -------------------------------------------------
    # Remove explicit continuation headings.
    #
    # Examples:
    # Question 7 — Continued
    # Question 7 - Continuation
    # -------------------------------------------------

    text = re.sub(
        r"(?im)^\s*"
        r"Question\s+\d+"
        r"\s*[-–—:]\s*"
        r"(?:Continued|Continuation|Contd\.?)"
        r"\s*$",
        "",
        text,
    )

    # -------------------------------------------------
    # Remove excessive blank lines.
    # -------------------------------------------------

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return "\n".join(lines).strip()


def parse_options(
    text: str,
) -> tuple[str, list[dict]]:

    option_matches = list(
        OPTION_PATTERN.finditer(text)
    )

    if not option_matches:

        cleaned_text = clean_question_text(
            text
        )

        return cleaned_text, []

    question_text = text[
        :option_matches[0].start()
    ].strip()

    options = []

    for index, match in enumerate(
        option_matches
    ):

        label = match.group(1).strip()

        option_start = match.end()

        if index + 1 < len(option_matches):

            option_end = matches_end = (
                option_matches[index + 1].start()
            )

        else:

            option_end = len(text)

        option_text = text[
            option_start:option_end
        ].strip()

        option_text = clean_question_text(
            option_text
        )

        option_text = " ".join(
            line.strip()
            for line in option_text.splitlines()
            if line.strip()
        )

        options.append(
            {
                "option_label": label,
                "option_text": option_text,
            }
        )

    question_text = clean_question_text(
        question_text
    )

    return question_text, options


def build_question(
    question_number: str,
    text: str,
) -> dict:

    text = clean_question_text(
        text
    )

    question_text, options = parse_options(
        text
    )

    question_text = clean_question_text(
        question_text
    )

    return {
        "question_number": question_number,
        "question_text": question_text,
        "options": options,
    }


def extract_questions_from_text(
    text: str,
) -> list[dict]:

    normalized_text = (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    matches = list(
        QUESTION_PATTERN.finditer(
            normalized_text
        )
    )

    questions = []

    for index, match in enumerate(matches):

        question_number = (
            match.group(1)
            or match.group(2)
            or match.group(3)
        )

        first_line = match.group(4).strip()

        # -------------------------------------------------
        # Ignore explicit continuation headings.
        #
        # Example:
        # Question 7 — Continued
        # -------------------------------------------------

        if is_continuation(first_line):
            continue

        # -------------------------------------------------
        # Ordinary numbered lines are only treated as
        # questions when they look question-like.
        #
        # Exception:
        # If the next marker is a continuation heading,
        # this is a real question even if it doesn't begin
        # with "what", "why", "how", etc.
        # -------------------------------------------------

        if match.group(3) is not None:

            followed_by_continuation = False

            if index + 1 < len(matches):

                next_first_line = matches[
                    index + 1
                ].group(4).strip()

                followed_by_continuation = (
                    is_continuation(
                        next_first_line
                    )
                )

            if (
                not looks_like_question(
                    first_line
                )
                and not followed_by_continuation
            ):
                continue

        # -------------------------------------------------
        # Determine the end of the current question.
        # -------------------------------------------------

        start = match.end()

        if index + 1 < len(matches):

            end = matches[
                index + 1
            ].start()

        else:

            end = len(
                normalized_text
            )

        remaining_text = normalized_text[
            start:end
        ].strip()

        # -------------------------------------------------
        # Check whether the next question marker is
        # actually a continuation heading.
        # -------------------------------------------------

        next_match_is_continuation = False

        if index + 1 < len(matches):

            next_first_line = matches[
                index + 1
            ].group(4).strip()

            next_match_is_continuation = (
                is_continuation(
                    next_first_line
                )
            )

        # -------------------------------------------------
        # Combine continuation text with the current
        # question.
        #
        # Example:
        #
        # 7. This question intentionally continues...
        #
        # --- PAGE 3 ---
        #
        # Question 7 — Continued
        # Explain how asynchronous processing...
        # Discuss the role of a message broker...
        # -------------------------------------------------

        if next_match_is_continuation:

            continuation_start = matches[
                index + 1
            ].end()

            if index + 2 < len(matches):

                continuation_end = matches[
                    index + 2
                ].start()

            else:

                continuation_end = len(
                    normalized_text
                )

            continuation_text = normalized_text[
                continuation_start:
                continuation_end
            ].strip()

            remaining_text = "\n".join(
                part
                for part in [
                    remaining_text,
                    continuation_text,
                ]
                if part
            )

        # -------------------------------------------------
        # Build the complete question.
        # -------------------------------------------------

        full_text = "\n".join(
            part
            for part in [
                first_line,
                remaining_text,
            ]
            if part
        )

        question = build_question(
            question_number,
            full_text,
        )

        questions.append(
            question
        )

    return questions