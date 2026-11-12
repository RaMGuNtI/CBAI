from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.backend.schemas.chatbot import ChatbotResponse


class DashboardMetricsResponse(BaseModel):
    total_chatbots: int
    total_documents: int
    total_conversations: int
    total_questions: int
    recent_chatbots: List[ChatbotResponse] = []

