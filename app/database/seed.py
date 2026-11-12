import os
from pathlib import Path
from fastapi import UploadFile
from app.database.connection import SessionLocal, init_db
from app.database.models import Chatbot, Document
from app.backend.schemas.chatbot import ChatbotCreate, ConfigurationBase
from app.backend.services.chatbot_service import ChatbotService
from app.backend.services.document_service import DocumentService


def seed_demo_chatbot():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(Chatbot).filter(Chatbot.name == "Acme Support AI").first()
        if existing:
            print(f"Demo chatbot already exists with ID: {existing.id}")
            return existing.id

        print("🌱 Seeding Demo Chatbot 'Acme Support AI'...")
        create_data = ChatbotCreate(
            name="Acme Support AI",
            description="Official automated customer care and technical support assistant for Acme Innovations products, warranty, and pricing.",
            purpose="Answer customer questions accurately using approved product guides, pricing tables, and support FAQs.",
            welcome_message="Hello! I am your Acme Support Assistant. How can I help you today with warranty, products, or service pricing?",
            domain="Customer Support",
            domain_description="Enterprise customer care and technical documentation for hardware and cloud services.",
            configuration=ConfigurationBase(
                personality="Friendly",
                tone="Conversational",
                language="English",
                response_length="Medium",
                target_audience="Intermediate",
                response_format="Structured Markdown",
                exclusive_knowledge=True,
                enable_citations=True,
                chunk_size=400,
                chunk_overlap=40,
                top_k=3,
                similarity_threshold=0.20
            )
        )

        bot = ChatbotService.create(db, create_data)
        bot.is_published = True
        bot.bot_avatar = "🤖"
        bot.branding_color = "#4F46E5"
        db.commit()

        # Ingest sample documents
        sample_dir = Path(__file__).resolve().parent.parent.parent / "storage" / "sample_docs"
        if sample_dir.exists():
            for sample_path in sample_dir.glob("*.*"):
                try:
                    with open(sample_path, "rb") as f:
                        upload = UploadFile(
                            filename=sample_path.name,
                            file=f
                        )
                        doc = DocumentService.upload_and_process_file(
                            db=db,
                            chatbot_id=bot.id,
                            file=upload,
                            enable_ocr=False
                        )
                        print(f"  Indexed document: {doc.filename} ({doc.total_chunks} chunks)")
                except Exception as e:
                    print(f"  Warning loading {sample_path.name}: {e}")

        print(f"✅ Demo chatbot seeded successfully! ID: {bot.id}")
        return bot.id
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_chatbot()

