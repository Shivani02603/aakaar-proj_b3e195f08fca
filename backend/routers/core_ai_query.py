from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import DocumentChunk, ChatMessage, ChatSession
from database.config import get_db
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
import openai

# Initialize APIRouter
router = APIRouter(tags=["Core AI / Query"])

# OAuth2 dependency for JWT authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic schemas
class QueryRequest(BaseModel):
    query: str = Field(..., description="The user query to process.")

class ChunkCitation(BaseModel):
    chunk_id: UUID = Field(..., description="The ID of the document chunk.")
    content: str = Field(..., description="The content of the chunk.")
    metadata: dict = Field(..., description="Metadata associated with the chunk.")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer to the query.")
    citations: List[ChunkCitation] = Field(..., description="List of citations used to generate the answer.")

# Helper function to retrieve top relevant chunks
def retrieve_relevant_chunks(query: str, db: Session) -> List[DocumentChunk]:
    # Placeholder logic for retrieving top-5 relevant chunks
    # Replace with actual vector search logic
    chunks = db.query(DocumentChunk).limit(5).all()
    return chunks

# Helper function to generate answer using LLM
def generate_answer_with_citations(query: str, chunks: List[DocumentChunk]) -> QueryResponse:
    # Prepare context from chunks
    context = "\n".join([chunk.content for chunk in chunks])
    metadata = [chunk.metadata for chunk in chunks]

    # Call OpenAI or other LLM API
    try:
        response = openai.Completion.create(
            model="gpt-4",
            prompt=f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer concisely with citations:",
            max_tokens=300,
            temperature=0.7
        )
        answer = response.choices[0].text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error generating answer from LLM.")

    # Prepare citations
    citations = [
        ChunkCitation(chunk_id=chunk.id, content=chunk.content, metadata=chunk.metadata)
        for chunk in chunks
    ]

    return QueryResponse(answer=answer, citations=citations)

# Route: POST /query
@router.post("/query", response_model=QueryResponse)
async def ai_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    Process a user query, retrieve relevant chunks, and generate an answer with citations.
    """
    # Retrieve relevant chunks
    chunks = retrieve_relevant_chunks(request.query, db)

    if not chunks:
        raise HTTPException(status_code=404, detail="No relevant chunks found.")

    # Generate answer using LLM
    response = generate_answer_with_citations(request.query, chunks)

    return response