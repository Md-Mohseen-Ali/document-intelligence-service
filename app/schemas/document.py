from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    content_type: str
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class DocumentStatusResponse(BaseModel):
    id: int
    status: str
