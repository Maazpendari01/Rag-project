from groq import Groq
from config import get_settings
from typing import List, Dict

settings = get_settings()
client = Groq(api_key=settings.groq_api_key)

# ✅ Valid, supported Groq models (corrected)
VALID_MODELS = {
    "fast": "llama-3.1-8b-instant",
    "strong": "llama-3.1-70b-versatile",
    "gemma": "gemma-7b-it",
}


def call_llm(
    prompt: str,
    max_tokens: int = 1024,
    model: str = "llama-3.1-8b-instant"  # Fixed default
) -> str:
    """Call Groq LLM (non-streaming)"""
    try:
        if model not in VALID_MODELS.values():
            print(f"[Warning] Unsupported model '{model}'. Falling back to {VALID_MODELS['fast']}.")
            model = VALID_MODELS["fast"]

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content

    except Exception as e:
        raise Exception(f"Groq API error: {str(e)}")


def call_llm_streaming(
    prompt: str,
    max_tokens: int = 1024,
    model: str = "llama-3.1-8b-instant"  # Fixed default
):
    """Streaming LLM call"""
    try:
        if model not in VALID_MODELS.values():
            print(f"[Warning] Unsupported model '{model}'. Falling back to {VALID_MODELS['fast']}.")
            model = VALID_MODELS["fast"]

        stream = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=max_tokens,
            temperature=0.7,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        raise Exception(f"Groq API streaming error: {str(e)}")


def call_llm_with_context(
    query: str,
    context_chunks: List[Dict],
    max_tokens: int = 2048,
    model: str = "llama-3.1-8b-instant"  # Fixed default
) -> str:
    """Call LLM with retrieved context (RAG)"""
    context = "\n\n".join([
        f"[Chunk {i+1} from Document {chunk['document_id']}]:\n{chunk['text']}"
        for i, chunk in enumerate(context_chunks)
    ])

    prompt = f"""
You are a helpful assistant that answers questions using the user's uploaded documents.
Base your answer ONLY on the provided context below.

Context:
{context}

Question: {query}

Instructions:
- Only answer based on the given context.
- If unsure, say "I don't have enough information to answer that from the uploaded documents."
- Be concise and factual.
- Mention which document or chunk supports your answer when possible.

Answer:
""".strip()

    try:
        return call_llm(prompt, max_tokens, model)
    except Exception as e:
        raise Exception(f"LLM with context error: {str(e)}")


def call_llm_with_context_and_history(
    query: str,
    context_chunks: List[Dict],
    conversation_history: List[Dict] = None,
    max_tokens: int = 2048,
    model: str = "llama-3.1-8b-instant"  # Fixed default
) -> str:
    """
    Call LLM with retrieved context AND conversation history
    """
    # Combine context from chunks
    context = "\n\n".join([
        f"[Chunk {i+1} from Document {chunk['document_id']}]:\n{chunk['text']}"
        for i, chunk in enumerate(context_chunks)
    ])

    # Build system message
    system_message = f"""You are a helpful assistant. Answer questions based on the provided context and conversation history.

Context from documents:
{context}

Instructions:
- Use both context and conversation history
- Refer naturally to earlier messages when needed
- If the answer is not in context, say so
- Cite chunks when possible
"""

    # Build message sequence
    messages = [{"role": "system", "content": system_message}]

    if conversation_history:
        messages.extend(conversation_history[-10:])  # last 10 messages

    messages.append({"role": "user", "content": query})

    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content

    except Exception as e:
        raise Exception(f"LLM with context and history error: {str(e)}")
