from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from app.database.models import Chatbot, Document, Conversation, Message, UsageStatistics
from app.backend.schemas.analytics import DashboardMetricsResponse
from app.backend.schemas.chatbot import ChatbotResponse


class AnalyticsService:
    @staticmethod
    def get_dashboard_metrics(db: Session) -> DashboardMetricsResponse:
        total_chatbots = db.query(Chatbot).count()
        total_documents = db.query(Document).filter(Document.status == "indexed").count()
        total_conversations = db.query(Conversation).count()
        total_questions = db.query(Message).filter(Message.role == "user").count()

        recent_bots = db.query(Chatbot).order_by(Chatbot.created_at.desc()).limit(5).all()

        formatted_recent = []
        for bot in recent_bots:
            doc_cnt = db.query(Document).filter(Document.chatbot_id == bot.id).count()
            resp = ChatbotResponse.model_validate(bot)
            resp.document_count = doc_cnt
            formatted_recent.append(resp)

        return DashboardMetricsResponse(
            total_chatbots=total_chatbots,
            total_documents=total_documents,
            total_conversations=total_conversations,
            total_questions=total_questions,
            recent_chatbots=formatted_recent
        )

