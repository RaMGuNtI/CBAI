from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.backend.schemas.chat import ChatRequest, ChatResponse
from app.backend.services.chatbot_service import ChatbotService
from app.backend.services.chat_service import ChatService

router = APIRouter(prefix="/public", tags=["Public Access"])


@router.get("/chatbots/{share_token}")
def get_public_chatbot(share_token: str, db: Session = Depends(get_db)):
    bot = ChatbotService.get_by_share_token(db, share_token)
    if not bot:
        # Check by id as fallback
        bot = ChatbotService.get_by_id(db, share_token)

    if not bot or not bot.is_published:
        raise HTTPException(status_code=404, detail="Chatbot not found or not published.")

    # Return only public-safe presentation attributes
    return {
        "id": bot.id,
        "share_token": bot.share_token,
        "name": bot.name,
        "description": bot.description,
        "welcome_message": bot.welcome_message,
        "branding_color": bot.branding_color,
        "bot_avatar": bot.bot_avatar,
        "domain": bot.domain
    }


@router.post("/chatbots/{share_token}/chat", response_model=ChatResponse)
def public_chat(
    share_token: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    bot = ChatbotService.get_by_share_token(db, share_token)
    if not bot:
        bot = ChatbotService.get_by_id(db, share_token)

    if not bot or not bot.is_published:
        raise HTTPException(status_code=403, detail="This chatbot is currently private or unavailable.")

    return ChatService.process_chat(
        db=db,
        chatbot_id=bot.id,
        request=request,
        is_public=True
    )

