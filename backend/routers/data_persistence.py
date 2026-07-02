from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from database.models import ChatSession, ChatMessage
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(tags=["Data Persistence"])

# Pydantic schemas
class ChatSessionBase(BaseModel):
    id: UUID
    user_id: UUID
    document_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

class ChatSessionResponse(ChatSessionBase):
    pass

class ChatMessageBase(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    citations: dict
    created_at: datetime

class ChatMessageResponse(ChatMessageBase):
    pass

# Routes
@router.get("/sessions", response_model=List[ChatSessionResponse])
def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user["id"]).all()
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch chat sessions")

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_chat_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user["id"]).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch chat messages")

@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user["id"]).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.delete(session)
        db.commit()
        return {"detail": "Chat session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete chat session")