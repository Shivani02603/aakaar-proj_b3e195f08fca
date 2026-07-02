import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from database.models import Document, DocumentChunk
from database.config import get_db
from openai import OpenAI
from PyPDF2 import PdfReader

class DocumentProcessingService:
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    EMBEDDING_MODEL = "text-embedding-3-small"

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")

    @staticmethod
    def split_text_into_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    @staticmethod
    def generate_embeddings(chunks: List[str]) -> List[List[float]]:
        try:
            embeddings = []
            for chunk in chunks:
                response = OpenAI.embeddings(model=DocumentProcessingService.EMBEDDING_MODEL, input=chunk)
                embeddings.append(response["data"][0]["embedding"])
            return embeddings
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

    @staticmethod
    def create_document_chunks(document_id: uuid.UUID, chunks: List[str], embeddings: List[List[float]], db: Session):
        try:
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                document_chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    chunk_index=index,
                    content=chunk,
                    embedding=embedding,
                    metadata={}
                )
                db.add(document_chunk)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating document chunks: {str(e)}")

    @staticmethod
    def process_document(document_id: uuid.UUID, db: Session):
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="File not found on server")

        text = DocumentProcessingService.extract_text_from_pdf(document.file_path)
        chunks = DocumentProcessingService.split_text_into_chunks(text, DocumentProcessingService.CHUNK_SIZE, DocumentProcessingService.CHUNK_OVERLAP)
        embeddings = DocumentProcessingService.generate_embeddings(chunks)
        DocumentProcessingService.create_document_chunks(document_id, chunks, embeddings, db)

        document.status = "processed"
        document.processed_at = datetime.utcnow()
        db.commit()

    @staticmethod
    def create(document: Document, db: Session):
        try:
            db.add(document)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating document: {str(e)}")

    @staticmethod
    def get_by_id(document_id: uuid.UUID, db: Session) -> Document:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    @staticmethod
    def list_all(db: Session) -> List[Document]:
        return db.query(Document).all()

    @staticmethod
    def update(document_id: uuid.UUID, updates: dict, db: Session):
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        for key, value in updates.items():
            if hasattr(document, key):
                setattr(document, key, value)

        document.updated_at = datetime.utcnow()
        db.commit()

    @staticmethod
    def delete(document_id: uuid.UUID, db: Session):
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        db.delete(document)
        db.commit()