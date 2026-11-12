from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from datetime import datetime, timezone
from app.database.models import Chatbot, Conversation, Message, UsageStatistics
from app.backend.schemas.chat import ChatRequest, ChatResponse, SourceCitation
from app.rag.retrieval.retriever import RAGRetriever
from app.rag.generation.generator import LLMGenerator


class ChatService:
    @staticmethod
    def get_or_create_conversation(db: Session, chatbot_id: str, session_id: str) -> Conversation:
        conv = db.query(Conversation).filter(
            Conversation.chatbot_id == chatbot_id,
            Conversation.session_id == session_id
        ).first()

        if not conv:
            conv = Conversation(
                chatbot_id=chatbot_id,
                session_id=session_id
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

            # Update stats
            stats = db.query(UsageStatistics).filter(UsageStatistics.chatbot_id == chatbot_id).first()
            if stats:
                stats.total_conversations = (stats.total_conversations or 0) + 1
                db.commit()

        return conv

    @staticmethod
    def process_chat(
        db: Session,
        chatbot_id: str,
        request: ChatRequest,
        is_public: bool = False
    ) -> ChatResponse:
        bot = db.query(Chatbot).filter(Chatbot.id == chatbot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Chatbot not found")

        if is_public and not bot.is_published:
            raise HTTPException(status_code=403, detail="This chatbot is currently private and not published.")

        config = bot.configuration
        conv = ChatService.get_or_create_conversation(db, chatbot_id, request.session_id)

        # 1. Fetch recent conversation history
        past_messages = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at.asc()).all()

        history_list = [{"role": m.role, "content": m.content} for m in past_messages[-6:]]

        # 2. Retrieve relevant chunks
        top_k = getattr(config, "top_k", 4) if config else 4
        similarity_threshold = getattr(config, "similarity_threshold", 0.25) if config else 0.25
        retrieval_strategy = getattr(config, "retrieval_strategy", "similarity") if config else "similarity"
        enable_hybrid = getattr(config, "enable_hybrid", False) if config else False
        enable_reranking = getattr(config, "enable_reranking", False) if config else False
        embedding_model = getattr(config, "embedding_model", "all-MiniLM-L6-v2") if config else "all-MiniLM-L6-v2"

        retrieved_chunks = RAGRetriever.retrieve(
            chatbot_id=chatbot_id,
            query=request.message,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            retrieval_strategy=retrieval_strategy,
            enable_hybrid=enable_hybrid,
            enable_reranking=enable_reranking,
            embedding_model=embedding_model
        )

        # 3. Generate answer
        result = LLMGenerator.generate_response(
            chatbot=bot,
            config=config,
            question=request.message,
            retrieved_chunks=retrieved_chunks,
            conversation_history=history_list
        )

        # 4. Save User Message
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=request.message,
            sources_json=[],
            latency_ms=0.0,
            tokens_used=len(request.message.split())
        )
        db.add(user_msg)

        # 5. Save Assistant Message
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=result["answer"],
            sources_json=result["sources"],
            latency_ms=result["latency_ms"],
            tokens_used=result["tokens_used"]
        )
        db.add(assistant_msg)

        # 6. Update usage stats
        stats = db.query(UsageStatistics).filter(UsageStatistics.chatbot_id == chatbot_id).first()
        if stats:
            stats.total_queries = (stats.total_queries or 0) + 1
            stats.last_queried_at = datetime.now(timezone.utc)

        db.commit()

        # Format citations
        citations = [
            SourceCitation(
                chunk_id=s.get("chunk_id"),
                filename=s.get("filename", "unknown"),
                page_number=s.get("page_number", 1),
                similarity=s.get("similarity", 0.0),
                snippet=s.get("snippet", "")
            )
            for s in result["sources"]
        ]

        return ChatResponse(
            answer=result["answer"],
            sources=citations,
            latency_ms=result["latency_ms"],
            tokens_used=result["tokens_used"],
            provider=result["provider"],
            session_id=conv.session_id
        )

    @staticmethod
    def get_conversation_history(db: Session, chatbot_id: str, session_id: str) -> Optional[Conversation]:
        return db.query(Conversation).filter(
            Conversation.chatbot_id == chatbot_id,
            Conversation.session_id == session_id
        ).first()

    @staticmethod
    def clear_conversation(db: Session, chatbot_id: str, session_id: str) -> bool:
        conv = db.query(Conversation).filter(
            Conversation.chatbot_id == chatbot_id,
            Conversation.session_id == session_id
        ).first()

        if conv:
            db.delete(conv)
            db.commit()
            return True
        return False

