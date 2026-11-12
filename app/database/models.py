import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database.connection import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    chatbots = relationship("Chatbot", back_populates="user", cascade="all, delete-orphan")


class Chatbot(Base):
    __tablename__ = "chatbots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, default="")
    purpose = Column(Text, default="")
    welcome_message = Column(Text, default="Hello! How can I assist you today?")
    domain = Column(String(100), default="General Purpose")
    domain_description = Column(Text, default="")
    is_published = Column(Boolean, default=False)
    share_token = Column(String(64), unique=True, default=generate_uuid)
    branding_color = Column(String(20), default="#4F46E5")
    bot_avatar = Column(String(255), default="🤖")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="chatbots")
    configuration = relationship("ChatbotConfiguration", back_populates="chatbot", uselist=False, cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="chatbot", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="chatbot", cascade="all, delete-orphan")
    usage_statistics = relationship("UsageStatistics", back_populates="chatbot", uselist=False, cascade="all, delete-orphan")
    evaluation_runs = relationship("EvaluationRun", back_populates="chatbot", cascade="all, delete-orphan")


class ChatbotConfiguration(Base):
    __tablename__ = "chatbot_configurations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    chatbot_id = Column(String(36), ForeignKey("chatbots.id"), unique=True, nullable=False)

    # Personality & Tone
    personality = Column(String(50), default="Professional")  # Professional, Friendly, Casual, Technical, Academic, Customer Support, Custom
    tone = Column(String(50), default="Formal")  # Formal, Neutral, Friendly, Conversational
    language = Column(String(50), default="English")  # English, Hindi, Telugu, etc.
    response_length = Column(String(50), default="Medium")  # Short, Medium, Detailed
    target_audience = Column(String(50), default="Intermediate")  # Beginner, Intermediate, Expert
    custom_instructions = Column(Text, default="")
    behavioral_restrictions = Column(Text, default="")

    # Response Formatting
    response_format = Column(String(50), default="Structured Markdown")  # Paragraphs, Bullet Points, Numbered Lists, Tables, Structured Markdown, JSON
    json_schema = Column(Text, default="")  # Optional user-defined JSON schema
    fallback_response = Column(
        Text,
        default="I apologize, but I could not find relevant information in the provided knowledge base to answer your question."
    )
    max_response_tokens = Column(Integer, default=1024)
    exclusive_knowledge = Column(Boolean, default=True)  # Strictly rely on uploaded docs
    enable_citations = Column(Boolean, default=True)
    enable_markdown = Column(Boolean, default=True)

    # RAG Settings
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")
    top_k = Column(Integer, default=4)
    similarity_threshold = Column(Float, default=0.25)
    retrieval_strategy = Column(String(50), default="similarity")  # similarity, mmr, threshold
    enable_hybrid = Column(Boolean, default=False)
    enable_reranking = Column(Boolean, default=False)

    # LLM Settings
    llm_provider = Column(String(50), default="gemini")  # gemini, openai, mock
    llm_model = Column(String(100), default="gemini-1.5-flash")

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    chatbot = relationship("Chatbot", back_populates="configuration")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    chatbot_id = Column(String(36), ForeignKey("chatbots.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    file_type = Column(String(20), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    status = Column(String(50), default="uploaded")  # uploaded, processing, indexed, error
    total_chunks = Column(Integer, default=0)
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)

    chatbot = relationship("Chatbot", back_populates="documents")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    chatbot_id = Column(String(36), ForeignKey("chatbots.id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    chatbot = relationship("Chatbot", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources_json = Column(JSON, default=list)  # list of source objects (filename, page, chunk_id, score)
    latency_ms = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    conversation = relationship("Conversation", back_populates="messages")


class UsageStatistics(Base):
    __tablename__ = "usage_statistics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    chatbot_id = Column(String(36), ForeignKey("chatbots.id"), unique=True, nullable=False)
    total_queries = Column(Integer, default=0)
    total_documents = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    last_queried_at = Column(DateTime, nullable=True)

    chatbot = relationship("Chatbot", back_populates="usage_statistics")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    chatbot_id = Column(String(36), ForeignKey("chatbots.id"), nullable=False, index=True)
    test_samples_count = Column(Integer, default=0)
    retrieval_relevance = Column(Float, default=0.0)
    context_relevance = Column(Float, default=0.0)
    answer_relevance = Column(Float, default=0.0)
    faithfulness = Column(Float, default=0.0)
    correctness = Column(Float, default=0.0)
    detailed_results_json = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)

    chatbot = relationship("Chatbot", back_populates="evaluation_runs")

