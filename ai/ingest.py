import os
import tempfile
from fastapi import UploadFile
from pypdf import PdfReader
import tiktoken
from .embeddings import get_embedding
from ai.vector_store import VectorStore

async def chunk(text: str, chunk_size: int = 1000, overlap: int = 200):
    enc = tiktoken.get_encoding('cl100k_base')
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += chunk_size - overlap
    return chunks

async def ingest_pdf(file: UploadFile, session_id: str, user_id: str):
    contents = await file.read()
    original_filename = file.filename or "unknown.pdf"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1])
    tmp.write(contents)
    tmp.flush()
    file_path = tmp.name

    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        chunks = await chunk(text)
        metadata_list = []
        for i, chunk_text in enumerate(chunks):
            metadata = {
                'source_filename': original_filename,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'page_or_row': f"Page {i + 1}"
            }
            embedding = await get_embedding(chunk_text)
            metadata_list.append((chunk_text, embedding, metadata))

        vector_store = VectorStore(os.getenv("PGVECTOR_CONNECTION_STRING"))
        for chunk_text, embedding, metadata in metadata_list:
            await vector_store.insert(embedding, metadata)

    finally:
        os.unlink(file_path)