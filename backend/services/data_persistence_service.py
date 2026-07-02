import uuid
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models import ChatSession, ChatMessage
from database.config import get_db


class DataPersistenceService:
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
            raise HTTPException(status_code=500, detail="Failed to create chat session") from e

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
            raise HTTPException(status_code=500, detail="Failed to retrieve chat sessions") from e

    @staticmethod
    def update_chat_session(session_id: uuid.UUID, title: Optional[str], db: Session = Depends(get_db)) -> ChatSession:
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            
            if title:
                session.title = title
                session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(session)
            return session
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update chat session") from e

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
            raise HTTPException(status_code=500, detail="Failed to delete chat session") from e

    @staticmethod
    def create_chat_message(session_id: uuid.UUID, role: str, content: str, citations: Optional[dict], db: Session = Depends(get_db)) -> ChatMessage:
        try:
            new_message = ChatMessage(
                id=uuid.uuid4(),
                session_id=session_id,
                role=role,
                content=content,
                citations=citations,
                created_at=datetime.utcnow()
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create chat message") from e

    @staticmethod
    def get_chat_messages_by_session(session_id: uuid.UUID, db: Session = Depends(get_db)) -> List[ChatMessage]:
        try:
            messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
            if not messages:
                raise HTTPException(status_code=404, detail="No messages found for the given session")
            return messages
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail="Failed to retrieve chat messages") from e

    @staticmethod
    def delete_chat_messages_by_session(session_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
        try:
            messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
            if not messages:
                raise HTTPException(status_code=404, detail="No messages found for the given session")
            
            for message in messages:
                db.delete(message)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to delete chat messages") from e