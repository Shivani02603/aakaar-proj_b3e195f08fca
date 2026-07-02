import uuid
from typing import List, Dict, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk, ChatMessage, ChatSession
from database.config import get_db
from openai import OpenAI

class CoreAIQueryService:
    @staticmethod
    def create_chat_session(user_id: uuid.UUID, document_id: uuid.UUID, title: str, db: Session = Depends(get_db)) -> ChatSession:
        try:
            new_session = ChatSession(
                id=uuid.uuid4(),
                user_id=user_id,
                document_id=document_id,
                title=title,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            return new_session
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating chat session: {str(e)}")

    @staticmethod
    def get_chat_session_by_id(session_id: uuid.UUID, db: Session = Depends(get_db)) -> ChatSession:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return session

    @staticmethod
    def list_chat_sessions(user_id: uuid.UUID, db: Session = Depends(get_db)) -> List[ChatSession]:
        try:
            sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
            return sessions
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving chat sessions: {str(e)}")

    @staticmethod
    def delete_chat_session(session_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            db.delete(session)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting chat session: {str(e)}")

    @staticmethod
    def generate_answer_with_citations(query: str, user_id: uuid.UUID, db: Session = Depends(get_db)) -> Dict[str, str]:
        try:
            # Retrieve top-5 relevant chunks based on embeddings
            chunks = db.query(DocumentChunk).filter(DocumentChunk.user_id == user_id).order_by(DocumentChunk.embedding.desc()).limit(5).all()
            if not chunks:
                raise HTTPException(status_code=404, detail="No relevant chunks found")

            # Prepare content for LLM
            context = "\n".join([chunk.content for chunk in chunks])
            citations = {chunk.chunk_index: chunk.metadata for chunk in chunks}

            # Generate answer using LLM
            llm = OpenAI()
            response = llm.generate_answer(query=query, context=context)

            return {
                "answer": response,
                "citations": citations
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")