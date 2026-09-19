from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image

from app.core.config import settings


pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def preprocess_image(image: Image.Image) -> np.ndarray:
    image_array = np.array(image)

    gray = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY,
    )

    denoised = cv2.GaussianBlur(
        gray,
        (3, 3),
        0,
    )

    thresholded = cv2.threshold(
        denoised,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )[1]

    return thresholded


def extract_text_from_image(image: Image.Image) -> dict:
    processed_image = preprocess_image(image)

    data = pytesseract.image_to_data(
        processed_image,
        config="--psm 6",
        output_type=pytesseract.Output.DICT,
    )

    lines = {}

    confidences = []

    for index, text in enumerate(data["text"]):
        cleaned_text = text.strip()

        if not cleaned_text:
            continue

        try:
            confidence = float(data["conf"][index])

            if confidence >= 0:
                confidences.append(confidence)

        except (ValueError, TypeError):
            confidence = -1

        block_number = data["block_num"][index]
        paragraph_number = data["par_num"][index]
        line_number = data["line_num"][index]

        line_key = (
            block_number,
            paragraph_number,
            line_number,
        )

        lines.setdefault(line_key, [])

        lines[line_key].append(cleaned_text)

    ordered_lines = []

    for words in lines.values():
        line = " ".join(words).strip()

        if line:
            ordered_lines.append(line)

    extracted_text = "\n".join(ordered_lines)

    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences
        else 0.0
    )

    return {
        "text": extracted_text,
        "confidence": round(
            average_confidence / 100,
            3,
        ),
    }


def extract_text_from_image_file(image_path: str) -> dict:
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = Image.open(path)

    return extract_text_from_image(image)