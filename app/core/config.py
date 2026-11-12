import os
from pathlib import Path
from typing import List, Set
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
DOCUMENTS_DIR = STORAGE_DIR / "documents"
CHROMA_PERSIST_DIR = STORAGE_DIR / "chroma"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = "CustomBot AI - No-Code RAG Chatbot Builder"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "custombot-ai-super-secret-key-change-in-production-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Storage & DB
    DATABASE_URL: str = f"sqlite:///{str(STORAGE_DIR / 'custombot.db').replace(chr(92), '/')}"
    STORAGE_DIR: Path = STORAGE_DIR
    DOCUMENTS_DIR: Path = DOCUMENTS_DIR
    CHROMA_PERSIST_DIR: Path = CHROMA_PERSIST_DIR

    # Upload constraints
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: Set[str] = {
        "pdf", "docx", "txt", "csv", "xlsx", "pptx", "md", "json"
    }

    # Model providers
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_LLM_PROVIDER: str = "gemini"  # "gemini" | "openai" | "mock"
    DEFAULT_LLM_MODEL: str = "gemini-1.5-flash"
    DEFAULT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Server configuration
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 8501
    BACKEND_URL: str = "http://127.0.0.1:8000"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
