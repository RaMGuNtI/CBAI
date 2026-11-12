from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class SourceCitation(BaseModel):
    chunk_id: Optional[str] = None
    filename: str
    page_number: Optional[int] = 1
    similarity: float
    snippet: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_session"
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation] = []
    latency_ms: float
    tokens_used: int
    provider: str
    session_id: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources_json: List[Dict[str, Any]] = []
    latency_ms: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: str
    chatbot_id: str
    session_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    model_config = ConfigDict(from_attributes=True)
