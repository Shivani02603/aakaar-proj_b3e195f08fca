from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Table, MetaData
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict
from typing import List
from database.config import get_db
from database.models import User

router = APIRouter(tags=["Sessions"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Metadata instance for Table definitions
metadata = MetaData()

# SQLAlchemy Models
ChatSession = Table(
    "chat_sessions",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), nullable=False),
    Column("title", String, default="New Chat"),
    Column("created_at", DateTime, default=datetime.utcnow),
    extend_existing=True,
)

ChatMessage = Table(
    "chat_messages",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("session_id", UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False),
    Column("role", String, nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
    extend_existing=True,
)

# Pydantic Schemas
class SessionCreate(BaseModel):
    title: str = "New Chat"

class SessionResponse(BaseModel):
    id: str = Field(..., alias="id")
    user_id: str = Field(..., alias="user_id")
    title: str
    created_at: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)

class MessageCreate(BaseModel):
    role: str
    content: str

class MessageResponse(BaseModel):
    id: str = Field(..., alias="id")
    session_id: str = Field(..., alias="session_id")
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)

# Dependency
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Implementation similar to auth.py
    pass

# Routes
@router.get("/", response_model=List[SessionResponse])
async def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(ChatSession).filter(ChatSession.c.user_id == current_user.id).order_by(ChatSession.c.created_at.desc()).all()
    return sessions

@router.post("/", response_model=SessionResponse)
async def create_session(session_data: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_session = ChatSession.insert().values(user_id=current_user.id, title=session_data.title)
    db.execute(new_session)
    db.commit()
    created_session = db.query(ChatSession).filter(ChatSession.c.user_id == current_user.id).order_by(ChatSession.c.created_at.desc()).first()
    return created_session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.c.id == session_id, ChatSession.c.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.execute(ChatSession.delete().where(ChatSession.c.id == session_id))
    db.commit()
    return

@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def list_messages(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(ChatMessage).filter(ChatMessage.c.session_id == session_id).order_by(ChatMessage.c.created_at.asc()).all()
    return messages

@router.post("/{session_id}/messages", response_model=MessageResponse)
async def create_message(session_id: str, message_data: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.c.id == session_id, ChatSession.c.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    new_message = ChatMessage.insert().values(session_id=session_id, role=message_data.role, content=message_data.content)
    db.execute(new_message)
    db.commit()
    created_message = db.query(ChatMessage).filter(ChatMessage.c.session_id == session_id).order_by(ChatMessage.c.created_at.desc()).first()
    return created_message