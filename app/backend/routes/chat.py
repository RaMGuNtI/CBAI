from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.backend.schemas.chat import (
    ChatRequest, ChatResponse, ConversationResponse, MessageResponse
)
from app.backend.services.chat_service import ChatService

router = APIRouter(prefix="/chatbots/{chatbot_id}", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_with_bot(
    chatbot_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    return ChatService.process_chat(
        db=db,
        chatbot_id=chatbot_id,
        request=request,
        is_public=False
    )


@router.get("/conversations/{session_id}", response_model=ConversationResponse)
def get_conversation_history(
    chatbot_id: str,
    session_id: str,
    db: Session = Depends(get_db)
):
    conv = ChatService.get_conversation_history(db, chatbot_id, session_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation session not found")
    return conv


@router.delete("/conversations/{session_id}")
def clear_conversation_history(
    chatbot_id: str,
    session_id: str,
    db: Session = Depends(get_db)
):
    cleared = ChatService.clear_conversation(db, chatbot_id, session_id)
    if not cleared:
        raise HTTPException(status_code=404, detail="Conversation session not found")
    return {"message": "Conversation history cleared successfully", "session_id": session_id}

