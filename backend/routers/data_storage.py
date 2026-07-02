from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import DocumentChunk
from database.config import get_db
from datetime import datetime

router = APIRouter(tags=["Data Storage"])

# Pydantic schemas
class DocumentChunkBase(BaseModel):
    document_id: UUID
    chunk_index: int
    content: str
    embedding: List[float]
    metadata: dict

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkUpdate(BaseModel):
    content: str | None = None
    embedding: List[float] | None = None
    metadata: dict | None = None

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Dependency for JWT authentication (placeholder for actual implementation)
def get_current_user():
    # This function should validate the JWT and return the user object
    pass

# Routes
@router.get("/chunks", response_model=List[DocumentChunkResponse])
async def list_document_chunks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    chunks = db.query(DocumentChunk).all()
    return chunks

@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def get_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found")
    return chunk

@router.post("/chunks", response_model=DocumentChunkResponse, status_code=201)
async def create_document_chunk(
    chunk: DocumentChunkCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    new_chunk = DocumentChunk(**chunk.dict())
    db.add(new_chunk)
    db.commit()
    db.refresh(new_chunk)
    return new_chunk

@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def update_document_chunk(
    chunk_id: UUID,
    chunk_update: DocumentChunkUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found")
    
    for key, value in chunk_update.dict(exclude_unset=True).items():
        setattr(chunk, key, value)
    
    chunk.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(chunk)
    return chunk

@router.delete("/chunks/{chunk_id}", status_code=204)
async def delete_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found")
    
    db.delete(chunk)
    db.commit()
    return None