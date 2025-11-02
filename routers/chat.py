import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import crud

from schemas import (
    ConversationCreate, ConversationResponse, ConversationWithMessages,
    ConversationChatRequest, ChatRequest, ChatResponse, MessageResponse
)
from auth import get_current_user
from models import UserDB
from database import get_db
from llm import (
    call_llm,
    call_llm_streaming,
    call_llm_with_context,
    call_llm_with_context_and_history
)
from retrieval import search_similar_chunks

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, current_user: UserDB = Depends(get_current_user)):
    """Simple chat endpoint - just LLM, no RAG"""
    try:
        response = call_llm(
            prompt=request.message,
            max_tokens=request.max_tokens,
            model=request.model
        )
        return ChatResponse(response=response, model=request.model, sources=[])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest, current_user: UserDB = Depends(get_current_user)):
    """Streaming chat - get responses in real-time"""
    try:
        def generate():
            for chunk in call_llm_streaming(
                prompt=request.message,
                max_tokens=request.max_tokens,
                model=request.model
            ):
                yield f"data: {json.dumps({'text': chunk})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag", response_model=ChatResponse)
def chat_with_rag(request: ChatRequest, top_k: int = 5, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    """Chat with RAG - retrieves relevant document chunks then asks LLM"""
    try:
        print(f"[RAG] Query: {request.message}")
        # --- MODIFICATION 2 --- (Example of how to pass it to other endpoints)
        # We pass an empty list since this endpoint doesn't support filtering
        chunks = search_similar_chunks(
            db=db,
            query=request.message,
            user_id=current_user.id,
            top_k=top_k,
            document_ids=[]
        )

        if not chunks:
            return ChatResponse(response="I don't have any documents to answer from. Please upload documents first.", model=request.model, sources=[])

        response = call_llm_with_context(
            query=request.message,
            context_chunks=chunks,
            max_tokens=request.max_tokens,
            model=request.model
        )

        sources = [
            {
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "similarity": round(chunk["similarity"], 4),
                "text_preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
            }
            for chunk in chunks
        ]

        return ChatResponse(response=response, model=request.model, sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/history", response_model=ChatResponse)
def chat_with_rag_and_history(request: ChatRequest, top_k: int = 5, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    """Chat with both RAG and conversation history."""
    try:
        print(f"[RAG+History] Query: {request.message}")
        # --- MODIFICATION 3 --- (Example of how to pass it to other endpoints)
        # We pass an empty list since this endpoint doesn't support filtering
        chunks = search_similar_chunks(
            db=db,
            query=request.message,
            user_id=current_user.id,
            top_k=top_k,
            document_ids=[]
        )

        if not chunks:
            return ChatResponse(response="I don't have any documents to answer from. Please upload documents first.", model=request.model, sources=[])

        conversation_history = []  # Replace with your DB fetch logic

        response = call_llm_with_context_and_history(
            query=request.message,
            context_chunks=chunks,
            conversation_history=conversation_history,
            max_tokens=request.max_tokens,
            model=request.model
        )

        sources = [
            {
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "similarity": round(chunk["similarity"], 4),
                "text_preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
            }
            for chunk in chunks
        ]

        return ChatResponse(response=response, model=request.model, sources=sources)

    except Exception as e:
        print(f"[RAG+History] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    request: ConversationCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    conversation = crud.create_conversation(db, current_user.id, request.title)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": 0
    }


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user's conversations"""
    return crud.get_user_conversations(db, current_user.id)


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
def get_conversation(
    conversation_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a conversation with all messages"""
    conversation = crud.get_conversation_by_id(db, conversation_id, current_user.id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation"""
    success = crud.delete_conversation(db, conversation_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted", "id": conversation_id}


@router.post("/conversation-rag", response_model=ChatResponse)
def chat_with_conversation_memory(
    # --- CHANGE 1: Use the correct schema ---
    request: ConversationChatRequest,
    top_k: int = 5,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """RAG chat with conversation memory"""
    try:
        # Get or create conversation
        # --- CHANGE 2: Access conversation_id directly ---
        conversation_id = request.conversation_id

        if conversation_id:
            conversation = crud.get_conversation_by_id(db, conversation_id, current_user.id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation
            title = request.message[:50] + "..." if len(request.message) > 50 else request.message
            conversation = crud.create_conversation(db, current_user.id, title)

        print(f"[Conversation {conversation.id}] Processing: {request.message[:50]}...")
        if request.document_ids:
            print(f"[Conversation {conversation.id}] Filtering search to docs: {request.document_ids}")

        # Retrieve relevant chunks
        # --- CHANGE 3: Pass the document_ids to the search function ---
        chunks = search_similar_chunks(
            db=db,
            query=request.message,
            user_id=current_user.id,
            top_k=top_k,
            document_ids=request.document_ids # <-- This is the new part
        )

        if not chunks:
            crud.create_message(db, conversation.id, "user", request.message, [])

            # --- MODIFIED: Give a more specific response if docs were filtered ---
            if request.document_ids:
                response_text = "I couldn't find any relevant information in the selected documents."
            else:
                response_text = "I don't have any documents to answer from. Please upload documents first."

            crud.create_message(db, conversation.id, "assistant", response_text, [])

            return ChatResponse(
                response=response_text,
                model=request.model,
                sources=[],
                conversation_id=conversation.id
            )

        # Get conversation history
        history_messages = crud.get_conversation_messages(db, conversation.id, limit=10)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in history_messages
        ]

        print(f"[Conversation {conversation.id}] Using {len(conversation_history)} previous messages")

        # Generate response
        response_text = call_llm_with_context_and_history(
            query=request.message,
            context_chunks=chunks,
            conversation_history=conversation_history,
            max_tokens=request.max_tokens,
            model=request.model
        )

        # Save messages
        sources = [
            {
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "similarity": round(chunk["similarity"], 4)
            }
            for chunk in chunks
        ]

        crud.create_message(db, conversation.id, "user", request.message, [])
        crud.create_message(db, conversation.id, "assistant", response_text, sources)

        print(f"[Conversation {conversation.id}] Response generated")

        return ChatResponse(
            response=response_text,
            model=request.model,
            sources=sources,
            conversation_id=conversation.id
        )

    except Exception as e:
        print(f"[Conversation] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
