from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.backend.schemas.document import DocumentResponse, DocumentUploadStatus
from app.backend.services.document_service import DocumentService

router = APIRouter(prefix="/chatbots/{chatbot_id}/documents", tags=["Documents"])


@router.get("", response_model=List[DocumentResponse])
def list_documents(chatbot_id: str, db: Session = Depends(get_db)):
    return DocumentService.get_by_chatbot(db, chatbot_id)


@router.post("/upload", response_model=List[DocumentUploadStatus])
async def upload_documents(
    chatbot_id: str,
    files: List[UploadFile] = File(...),
    enable_ocr: bool = Form(False),
    db: Session = Depends(get_db)
):
    results: List[DocumentUploadStatus] = []

    for file in files:
        try:
            doc = DocumentService.upload_and_process_file(
                db=db,
                chatbot_id=chatbot_id,
                file=file,
                enable_ocr=enable_ocr
            )
            results.append(
                DocumentUploadStatus(
                    document_id=doc.id,
                    filename=doc.filename,
                    status=doc.status,
                    total_chunks=doc.total_chunks,
                    message="Indexed successfully"
                )
            )
        except HTTPException as e:
            results.append(
                DocumentUploadStatus(
                    document_id="",
                    filename=file.filename or "unknown",
                    status="error",
                    total_chunks=0,
                    message=e.detail
                )
            )
        except Exception as e:
            results.append(
                DocumentUploadStatus(
                    document_id="",
                    filename=file.filename or "unknown",
                    status="error",
                    total_chunks=0,
                    message=f"Failed: {str(e)}"
                )
            )

    return results


@router.delete("/{document_id}")
def delete_document(chatbot_id: str, document_id: str, db: Session = Depends(get_db)):
    success = DocumentService.delete_document(db, chatbot_id, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully", "document_id": document_id}

