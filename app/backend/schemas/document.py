from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    chatbot_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    total_chunks: int
    error_message: Optional[str] = ""
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentUploadStatus(BaseModel):
    document_id: str
    filename: str
    status: str
    total_chunks: int
    message: str
