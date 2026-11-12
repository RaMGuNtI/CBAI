from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class ConfigurationBase(BaseModel):
    personality: str = "Professional"
    tone: str = "Formal"
    language: str = "English"
    response_length: str = "Medium"
    target_audience: str = "Intermediate"
    custom_instructions: str = ""
    behavioral_restrictions: str = ""

    response_format: str = "Structured Markdown"
    json_schema: str = ""
    fallback_response: str = "I apologize, but I could not find relevant information in the provided knowledge base to answer your question."
    max_response_tokens: int = 1024
    exclusive_knowledge: bool = True
    enable_citations: bool = True
    enable_markdown: bool = True

    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_model: str = "all-MiniLM-L6-v2"
    top_k: int = 4
    similarity_threshold: float = 0.25
    retrieval_strategy: str = "similarity"
    enable_hybrid: bool = False
    enable_reranking: bool = False

    llm_provider: str = "gemini"
    llm_model: str = "gemini-1.5-flash"


class ConfigurationUpdate(ConfigurationBase):
    pass


class ConfigurationResponse(ConfigurationBase):
    id: str
    chatbot_id: str
    model_config = ConfigDict(from_attributes=True)


class ChatbotCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = ""
    purpose: Optional[str] = ""
    welcome_message: Optional[str] = "Hello! How can I assist you today?"
    domain: Optional[str] = "General Purpose"
    domain_description: Optional[str] = ""
    configuration: Optional[ConfigurationBase] = None


class ChatbotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    welcome_message: Optional[str] = None
    domain: Optional[str] = None
    domain_description: Optional[str] = None
    is_published: Optional[bool] = None
    branding_color: Optional[str] = None
    bot_avatar: Optional[str] = None
    configuration: Optional[ConfigurationUpdate] = None


class ChatbotResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    purpose: Optional[str] = ""
    welcome_message: str
    domain: str
    domain_description: Optional[str] = ""
    is_published: bool
    share_token: str
    branding_color: str
    bot_avatar: str
    created_at: datetime
    updated_at: datetime
    configuration: Optional[ConfigurationResponse] = None
    document_count: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)


class PublishStatusUpdate(BaseModel):
    is_published: bool
