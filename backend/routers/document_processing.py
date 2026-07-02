from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from database.models import Document, DocumentChunk
from database.config import get_db
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(tags=["Document Processing"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


class DocumentProcessingRequest(BaseModel):
    document_id: UUID


class DocumentProcessingResponse(BaseModel):
    document_id: UUID
    status: str
    processed_at: datetime


class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    embedding: List[float]
    metadata: dict


def get_current_user(token: str = Depends(oauth2_scheme)):
    # Placeholder for JWT token validation logic
    # Replace with actual implementation
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"user_id": "mock_user_id"}  # Replace with actual user extraction logic


def extract_text_from_pdf(file_path: str) -> str:
    # Inline implementation for extracting text from a PDF file
    # Replace with actual PDF processing logic
    return "Extracted text from PDF"


def split_text_into_chunks(text: str, chunk_size: int, overlap: int) -> List[dict]:
    # Inline implementation for splitting text into chunks
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_content = text[start:end]
        chunks.append({"content": chunk_content, "metadata": {}})
        start = end - overlap
    return chunks


def generate_embeddings(text: str) -> List[float]:
    # Inline implementation for generating embeddings
    # Replace with actual embedding generation logic
    return [0.0] * 128  # Example: 128-dimensional zero vector


@router.post("/process", response_model=DocumentProcessingResponse)
async def process_document(
    request: DocumentProcessingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Process a document by extracting text, splitting into chunks, and generating embeddings.
    """
    document = db.query(Document).filter(Document.id == request.document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        # Extract text from the document
        extracted_text = extract_text_from_pdf(document.file_path)

        # Split text into chunks
        chunks = split_text_into_chunks(extracted_text, chunk_size=1000, overlap=200)

        # Generate embeddings for each chunk
        for index, chunk in enumerate(chunks):
            embedding = generate_embeddings(chunk["content"])
            document_chunk = DocumentChunk(
                id=UUID(),
                document_id=document.id,
                chunk_index=index,
                content=chunk["content"],
                embedding=embedding,
                metadata=chunk["metadata"],
            )
            db.add(document_chunk)

        document.status = "processed"
        document.processed_at = datetime.utcnow()
        db.commit()

        return DocumentProcessingResponse(
            document_id=document.id,
            status=document.status,
            processed_at=document.processed_at,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/chunks/{document_id}", response_model=List[DocumentChunkResponse])
async def get_document_chunks(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve all chunks for a specific document.
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()

    return [
        DocumentChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=chunk.metadata,
        )
        for chunk in chunks
    ]