from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import DocumentChunkDB, DocumentDB
from embeddings import generate_query_embedding
from typing import List, Dict
import numpy as np

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors

    Returns value between -1 and 1:
    - 1 means vectors are identical
    - 0 means vectors are orthogonal (unrelated)
    - -1 means vectors are opposite
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def search_similar_chunks(
    db: Session,
    query: str,
    user_id: int,
    top_k: int = 5,
    document_ids: List[int] = None
) -> List[Dict]:
    """
    Find chunks most similar to the query using cosine similarity

    Args:
        db: Database session
        query: User's search query
        user_id: Current user ID (for access control)
        top_k: Number of results to return
        document_ids: Optional list of specific document IDs to search

    Returns:
        List of chunks with similarity scores, sorted by relevance
    """
    # Generate embedding for the query
    print(f"Generating embedding for query: {query[:50]}...")
    query_embedding = generate_query_embedding(query)

    # Build query to get all chunks for this user
    query_obj = db.query(DocumentChunkDB).join(
        DocumentDB, DocumentChunkDB.document_id == DocumentDB.id
    )

    # Filter by user
    query_obj = query_obj.filter(DocumentDB.user_id == user_id)

    # Filter by specific documents if provided
    if document_ids:
        query_obj = query_obj.filter(DocumentDB.id.in_(document_ids))

    # Only get chunks that have embeddings
    query_obj = query_obj.filter(DocumentChunkDB.embedding.isnot(None))

    chunks = query_obj.all()

    if not chunks:
        print("No chunks found with embeddings")
        return []

    print(f"Calculating similarity for {len(chunks)} chunks...")

    # Calculate similarity for each chunk
    results = []
    for chunk in chunks:
        if chunk.embedding:
            try:
                similarity = cosine_similarity(query_embedding, chunk.embedding)
                results.append({
                    "id": chunk.id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                    "token_count": chunk.token_count,
                    "similarity": similarity
                })
            except Exception as e:
                print(f"Error calculating similarity for chunk {chunk.id}: {e}")
                continue

    # Sort by similarity (highest first)
    results.sort(key=lambda x: x["similarity"], reverse=True)

    # Fixed print statement
    if results:
        print(f"Top similarity score: {results[0]['similarity']:.4f}")
    else:
        print("Top similarity score: N/A")

    # Return top_k results
    return results[:top_k]
