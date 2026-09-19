from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


STORAGE_DIR = Path("storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}


def save_upload(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("Unsupported file type")

    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file extension")

    storage_key = f"{uuid4()}{extension}"
    file_path = STORAGE_DIR / storage_key

    total_size = 0

    try:
        with file_path.open("wb") as output:
            while chunk := file.file.read(1024 * 1024):
                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise ValueError(
                        "File size exceeds the maximum limit of 10 MB"
                    )

                output.write(chunk)

    except Exception:
        if file_path.exists():
            file_path.unlink()

        raise

    return storage_key