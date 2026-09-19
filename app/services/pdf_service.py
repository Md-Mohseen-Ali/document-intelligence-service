from pathlib import Path

import fitz

from app.services.ocr_service import extract_text_from_image


STORAGE_DIR = Path("storage")


def extract_pdf_pages(
    storage_key: str,
) -> list[dict]:

    file_path = STORAGE_DIR / storage_key

    if not file_path.exists():
        raise FileNotFoundError(
            f"Stored document not found: {storage_key}"
        )

    pages = []

    with fitz.open(file_path) as pdf:

        for page_index, page in enumerate(pdf):

            page_number = page_index + 1

            # -------------------------------------------------
            # First try normal PDF text extraction.
            # -------------------------------------------------

            text = page.get_text("text").strip()

            # -------------------------------------------------
            # Digital PDF
            # -------------------------------------------------

            if text:

                pages.append(
                    {
                        "page_number": page_number,
                        "extracted_text": text,
                        "is_scanned": False,
                        "ocr_confidence": None,
                    }
                )

                continue

            # -------------------------------------------------
            # Scanned PDF
            #
            # Render the page as an image and send it
            # through OCR.
            # -------------------------------------------------

            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                alpha=False,
            )

            image_bytes = pixmap.tobytes(
                "png"
            )

            from PIL import Image
            from io import BytesIO

            image = Image.open(
                BytesIO(image_bytes)
            )

            ocr_result = extract_text_from_image(
                image
            )

            pages.append(
                {
                    "page_number": page_number,
                    "extracted_text": ocr_result[
                        "text"
                    ],
                    "is_scanned": True,
                    "ocr_confidence": ocr_result[
                        "confidence"
                    ],
                }
            )

    return pages