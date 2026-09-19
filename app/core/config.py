from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = (
        "Document Intelligence & Question Extraction Service"
    )

    app_version: str = "1.0.0"

    debug: bool = True

    database_url: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    celery_broker_url: str
    celery_result_backend: str

    tesseract_cmd: str = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()