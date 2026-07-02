import os
from .embeddings import get_embedding
import openai

async def search_vectors(embedding: list[float], top_k: int) -> list[dict]:
    # Placeholder implementation for search_vectors
    # Replace with actual vector search logic
    return [{'text': 'Sample text', 'source_filename': 'example.pdf', 'page_or_row': '1'}]

async def retrieve_context(query: str, top_k: int, session_id: str, user_id: str):
    embedding = await get_embedding(query)
    results = await search_vectors(embedding, top_k)
    return results

async def answer_question(query: str, session_id: str, user_id: str) -> dict:
    context_chunks = await retrieve_context(query, top_k=5, session_id=session_id, user_id=user_id)
    sources = [{'filename': m['source_filename'], 'location': m['page_or_row']} for m in context_chunks]

    if not sources:
        return {'answer': "No relevant information found.", 'sources': []}

    context_text = "\n".join([chunk['text'] for chunk in context_chunks])
    prompt = f"Answer the following question based on the context:\n\nContext:\n{context_text}\n\nQuestion:\n{query}"

    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai.api_key = openai_api_key
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{'role': 'user', 'content': prompt}]
    )
    answer = response.choices[0].message.content

    return {'answer': answer, 'sources': sources}