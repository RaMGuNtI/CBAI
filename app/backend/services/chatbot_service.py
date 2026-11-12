from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException
from app.database.models import Chatbot, ChatbotConfiguration, UsageStatistics
from app.backend.schemas.chatbot import ChatbotCreate, ChatbotUpdate
from app.rag.vector_store.chroma_manager import ChromaManager


class ChatbotService:
    @staticmethod
    def get_all(db: Session, user_id: Optional[str] = None) -> List[Chatbot]:
        query = db.query(Chatbot)
        if user_id:
            query = query.filter(Chatbot.user_id == user_id)
        return query.order_by(Chatbot.created_at.desc()).all()

    @staticmethod
    def get_by_id(db: Session, chatbot_id: str) -> Optional[Chatbot]:
        return db.query(Chatbot).filter(Chatbot.id == chatbot_id).first()

    @staticmethod
    def get_by_share_token(db: Session, share_token: str) -> Optional[Chatbot]:
        return db.query(Chatbot).filter(Chatbot.share_token == share_token).first()

    @staticmethod
    def create(db: Session, data: ChatbotCreate, user_id: Optional[str] = None) -> Chatbot:
        bot = Chatbot(
            user_id=user_id,
            name=data.name,
            description=data.description or "",
            purpose=data.purpose or "",
            welcome_message=data.welcome_message or "Hello! How can I assist you today?",
            domain=data.domain or "General Purpose",
            domain_description=data.domain_description or ""
        )
        db.add(bot)
        db.flush()

        # Initialize default or user-provided configuration
        cfg_data = data.configuration.model_dump() if data.configuration else {}
        config = ChatbotConfiguration(
            chatbot_id=bot.id,
            **cfg_data
        )
        db.add(config)

        # Initialize usage statistics
        stats = UsageStatistics(chatbot_id=bot.id)
        db.add(stats)

        db.commit()
        db.refresh(bot)
        return bot

    @staticmethod
    def update(db: Session, chatbot_id: str, data: ChatbotUpdate) -> Chatbot:
        bot = ChatbotService.get_by_id(db, chatbot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Chatbot not found")

        update_dict = data.model_dump(exclude_unset=True)

        if "configuration" in update_dict and update_dict["configuration"]:
            cfg_dict = update_dict.pop("configuration")
            if bot.configuration:
                for k, v in cfg_dict.items():
                    setattr(bot.configuration, k, v)
            else:
                new_cfg = ChatbotConfiguration(chatbot_id=bot.id, **cfg_dict)
                db.add(new_cfg)

        for k, v in update_dict.items():
            if hasattr(bot, k):
                setattr(bot, k, v)

        db.commit()
        db.refresh(bot)
        return bot

    @staticmethod
    def set_publish_status(db: Session, chatbot_id: str, is_published: bool) -> Chatbot:
        bot = ChatbotService.get_by_id(db, chatbot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Chatbot not found")

        bot.is_published = is_published
        db.commit()
        db.refresh(bot)
        return bot

    @staticmethod
    def delete(db: Session, chatbot_id: str) -> bool:
        bot = ChatbotService.get_by_id(db, chatbot_id)
        if not bot:
            return False

        # Cleanup isolated vector collection
        ChromaManager.delete_chatbot_collection(chatbot_id)

        db.delete(bot)
        db.commit()
        return True

