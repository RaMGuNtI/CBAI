import shutil
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from app.core.config import settings
from app.core.security import sanitize_filename
from app.database.models import Document, Chatbot, UsageStatistics
from app.rag.loaders.registry import registry
from app.rag.chunking.chunker import DocumentChunker
from app.rag.vector_store.chroma_manager import ChromaManager


class DocumentService:
    @staticmethod
    def get_by_chatbot(db: Session, chatbot_id: str) -> List[Document]:
        return db.query(Document).filter(Document.chatbot_id == chatbot_id).order_by(Document.created_at.desc()).all()

    @staticmethod
    def get_by_id(db: Session, document_id: str) -> Optional[Document]:
        return db.query(Document).filter(Document.id == document_id).first()

    @staticmethod
    def upload_and_process_file(
        db: Session,
        chatbot_id: str,
        file: UploadFile,
        enable_ocr: bool = False
    ) -> Document:
        bot = db.query(Chatbot).filter(Chatbot.id == chatbot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Chatbot not found")

        raw_filename = file.filename or "uploaded_file"
        safe_name = sanitize_filename(raw_filename)
        ext = Path(safe_name).suffix.lower()

        # Temporary destination for validation & hashing
        bot_doc_dir = settings.DOCUMENTS_DIR / chatbot_id
        bot_doc_dir.mkdir(parents=True, exist_ok=True)
        dest_path = bot_doc_dir / safe_name

        # Save uploaded file
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = dest_path.stat().st_size

        try:
            # 1. Validate file format and size
            registry.validate_file(safe_name, file_size)

            # 2. Check duplicate files via hash
            file_hash = registry.calculate_file_hash(dest_path)
            existing_doc = db.query(Document).filter(
                Document.chatbot_id == chatbot_id,
                Document.file_hash == file_hash
            ).first()

            if existing_doc:
                dest_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate file detected: '{safe_name}' has already been uploaded to this chatbot."
                )

            # 3. Create document record in database
            doc_record = Document(
                chatbot_id=chatbot_id,
                filename=safe_name,
                file_hash=file_hash,
                file_type=ext.replace(".", "").upper(),
                file_size_bytes=file_size,
                storage_path=str(dest_path),
                status="processing"
            )
            db.add(doc_record)
            db.commit()
            db.refresh(doc_record)

            # 4. Extract pages using registered loader
            pages = registry.load_document(dest_path, enable_ocr=enable_ocr)

            # 5. Chunk extracted text using chatbot configuration
            config = bot.configuration
            chunk_size = getattr(config, "chunk_size", 500) if config else 500
            chunk_overlap = getattr(config, "chunk_overlap", 50) if config else 50
            embedding_model = getattr(config, "embedding_model", "all-MiniLM-L6-v2") if config else "all-MiniLM-L6-v2"

            chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = chunker.chunk_pages(
                pages=pages,
                chatbot_id=chatbot_id,
                document_id=doc_record.id,
                filename=safe_name
            )

            # 6. Index into isolated ChromaDB collection
            if chunks:
                ChromaManager.add_chunks(
                    chatbot_id=chatbot_id,
                    chunks=chunks,
                    embedding_model_name=embedding_model
                )

            # 7. Update document status and stats
            doc_record.status = "indexed"
            doc_record.total_chunks = len(chunks)

            stats = db.query(UsageStatistics).filter(UsageStatistics.chatbot_id == chatbot_id).first()
            if stats:
                stats.total_documents = db.query(Document).filter(Document.chatbot_id == chatbot_id, Document.status == "indexed").count()
                stats.total_chunks = (stats.total_chunks or 0) + len(chunks)

            db.commit()
            db.refresh(doc_record)
            return doc_record

        except Exception as e:
            if 'doc_record' in locals():
                doc_record.status = "error"
                doc_record.error_message = str(e)
                db.commit()
            raise HTTPException(status_code=400, detail=f"Document processing failed: {str(e)}")

    @staticmethod
    def delete_document(db: Session, chatbot_id: str, document_id: str) -> bool:
        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.chatbot_id == chatbot_id
        ).first()

        if not doc:
            return False

        # 1. Remove vector chunks from isolated collection
        try:
            ChromaManager.delete_document_chunks(chatbot_id=chatbot_id, document_id=document_id)
        except Exception:
            pass

        # 2. Remove physical file
        try:
            path = Path(doc.storage_path)
            if path.exists():
                path.unlink()
        except Exception:
            pass

        # 3. Update statistics
        stats = db.query(UsageStatistics).filter(UsageStatistics.chatbot_id == chatbot_id).first()
        if stats:
            stats.total_chunks = max(0, (stats.total_chunks or 0) - doc.total_chunks)
            stats.total_documents = max(0, (stats.total_documents or 1) - 1)

        db.delete(doc)
        db.commit()
        return True

