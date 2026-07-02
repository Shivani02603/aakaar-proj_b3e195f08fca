from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from database.models import Document, User
from database.config import get_db
from backend.services.auth import get_current_user
import os
import shutil

router = APIRouter(tags=["Document Management"])

# Pydantic Schemas
class DocumentBase(BaseModel):
    filename: str
    file_path: str
    file_size: int
    status: str
    uploaded_at: datetime
    processed_at: datetime | None = None

class DocumentCreate(BaseModel):
    filename: str
    file_size: int

class DocumentResponse(DocumentBase):
    id: UUID
    user_id: UUID

# Routes
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF) for processing.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # Save file to server
    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save file.")

    # Create document record in the database
    document = Document(
        user_id=user.id,
        filename=file.filename,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        status="uploaded",
        uploaded_at=datetime.utcnow(),
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return document

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all documents uploaded by the authenticated user.
    """
    documents = db.query(Document).filter(Document.user_id == user.id).all()
    return documents

@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document by ID.
    """
    document = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove file from server
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete file.")

    # Remove document record from database
    db.delete(document)
    db.commit()

    return {"detail": "Document deleted successfully."}