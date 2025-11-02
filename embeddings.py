import voyageai
from config import get_settings
from typing import List

settings = get_settings()
vo = voyageai.Client(api_key=settings.voyage_api_key)

def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text

    Returns a vector of 1024 numbers representing the text
    """
    try:
        result = vo.embed(
            texts=[text],
            model="voyage-3",
            input_type="document"
        )
        return result.embeddings[0]

    except Exception as e:
        raise Exception(f"Embedding error: {str(e)}")


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts at once
    More efficient than calling generate_embedding multiple times
    """
    try:
        result = vo.embed(
            texts=texts,
            model="voyage-3",
            input_type="document"
        )
        return result.embeddings

    except Exception as e:
        raise Exception(f"Batch embedding error: {str(e)}")


def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for a search query

    Uses input_type="query" which is optimized for search queries
    vs input_type="document" which is for the documents themselves
    """
    try:
        result = vo.embed(
            texts=[query],
            model="voyage-3",
            input_type="query"
        )
        return result.embeddings[0]

    except Exception as e:
        raise Exception(f"Query embedding error: {str(e)}")
