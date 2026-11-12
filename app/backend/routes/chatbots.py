from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database.connection import get_db
from app.database.models import Document
from app.backend.schemas.chatbot import (
    ChatbotCreate, ChatbotUpdate, ChatbotResponse, PublishStatusUpdate
)
from app.backend.services.chatbot_service import ChatbotService
from app.backend.routes.auth import get_current_user_optional
from app.core.config import settings

router = APIRouter(prefix="/chatbots", tags=["Chatbots"])


def _enrich_bot_response(bot, db: Session) -> ChatbotResponse:
    doc_count = db.query(Document).filter(Document.chatbot_id == bot.id).count()
    resp = ChatbotResponse.model_validate(bot)
    resp.document_count = doc_count
    return resp


@router.get("", response_model=List[ChatbotResponse])
def list_chatbots(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    user_id = current_user.id if (current_user and hasattr(current_user, "id")) else None
    bots = ChatbotService.get_all(db, user_id=user_id)
    return [_enrich_bot_response(bot, db) for bot in bots]


@router.post("", response_model=ChatbotResponse)
def create_chatbot(
    data: ChatbotCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    user_id = current_user.id if (current_user and hasattr(current_user, "id")) else None
    bot = ChatbotService.create(db, data, user_id=user_id)
    return _enrich_bot_response(bot, db)


@router.get("/{chatbot_id}", response_model=ChatbotResponse)
def get_chatbot(chatbot_id: str, db: Session = Depends(get_db)):
    bot = ChatbotService.get_by_id(db, chatbot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    return _enrich_bot_response(bot, db)


@router.put("/{chatbot_id}", response_model=ChatbotResponse)
def update_chatbot(
    chatbot_id: str,
    data: ChatbotUpdate,
    db: Session = Depends(get_db)
):
    bot = ChatbotService.update(db, chatbot_id, data)
    return _enrich_bot_response(bot, db)


@router.delete("/{chatbot_id}")
def delete_chatbot(chatbot_id: str, db: Session = Depends(get_db)):
    success = ChatbotService.delete(db, chatbot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    return {"message": "Chatbot deleted successfully", "chatbot_id": chatbot_id}


@router.post("/{chatbot_id}/publish", response_model=ChatbotResponse)
def set_publish_status(
    chatbot_id: str,
    data: PublishStatusUpdate,
    db: Session = Depends(get_db)
):
    bot = ChatbotService.set_publish_status(db, chatbot_id, data.is_published)
    return _enrich_bot_response(bot, db)


@router.get("/{chatbot_id}/share")
def get_share_details(chatbot_id: str, db: Session = Depends(get_db)):
    bot = ChatbotService.get_by_id(db, chatbot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Chatbot not found")

    public_chat_url = f"{settings.BACKEND_URL}/public/{bot.share_token}"
    embed_snippet = (
        f'<!-- CustomBot AI Embed Widget -->\n'
        f'<script src="{settings.BACKEND_URL}/static/widget.js" '
        f'data-bot-id="{bot.share_token}" '
        f'data-color="{bot.branding_color}" '
        f'defer></script>'
    )

    return {
        "chatbot_id": bot.id,
        "name": bot.name,
        "is_published": bot.is_published,
        "share_token": bot.share_token,
        "public_url": public_chat_url,
        "embed_code": embed_snippet,
        "branding": {
            "color": bot.branding_color,
            "avatar": bot.bot_avatar
        }
    }
