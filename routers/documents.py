import os
import uuid
from typing import List
from retrieval import search_similar_chunks

import aiofiles
import magic
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename

import crud
from auth import get_current_user
from database import SessionLocal, get_db
from models import UserDB
from schemas import ChunkResponse, DocumentResponse
from text_processing import process_document_async

router = APIRouter(prefix="/documents", tags=["documents"])

# Configuration
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_file_type(content: bytes, filename: str) -> str:
    """Validate file type by checking actual content"""
    mime = magic.from_buffer(content, mime=True)

    if mime not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: PDF, TXT, DOCX. Got: {mime}",
        )

    return mime


def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename while preserving extension"""
    ext = os.path.splitext(original_filename)[1].lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{ext}"


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,  # No default - comes FIRST
    file: UploadFile = File(...),  # Has default
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload and process document in background"""

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024)}MB",
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Validate file type
    content_type = validate_file_type(content, file.filename)

    # Sanitize original filename
    original_filename = secure_filename(file.filename)

    # Generate unique filename
    unique_filename = generate_unique_filename(original_filename)

    # Create user directory
    user_dir = os.path.join(UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)

    # Full file path
    file_path = os.path.join(user_dir, unique_filename)

    # Save file to disk
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Save metadata to database
    document = crud.create_document(
        db=db,
        filename=unique_filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        content_type=content_type,
        user_id=current_user.id,
    )

    # Process document in background
    background_tasks.add_task(
        process_document_async, document.id, file_path, content_type, SessionLocal
    )

    return document


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all documents uploaded by current user"""
    return crud.get_user_documents(db, current_user.id)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get specific document"""
    document = crud.get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
def get_document_chunks(
    document_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all text chunks for a document"""
    document = crud.get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return crud.get_document_chunks(db, document_id)


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete document and its chunks"""
    document = crud.get_document_by_id(db, document_id, current_user.id)

    # 🧠 Fix: Handle None safely
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 🧠 Fix: Convert to string for type safety
    file_path = str(document.file_path) if document.file_path else None

    # Delete chunks first
    crud.delete_document_chunks(db, document_id)

    # Delete file from disk (safe check)
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    # Delete from database
    crud.delete_document(db, document_id, current_user.id)

    return {"message": "Document deleted successfully", "id": document_id}

@router.post("/search")
def search_documents(
    query: str,
    top_k: int = 5,
    document_ids: List[int] = None,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Semantic search across all your documents

    Args:
        query: What you're looking for (e.g., "How do I use FastAPI?")
        top_k: Number of results to return (default 5)
        document_ids: Optional - search only specific documents

    Returns:
        Most relevant chunks with similarity scores

    Example test:
    - Upload a document about Python
    - Search for "python web framework"
    - Get back relevant chunks even if exact words don't match
    """
    if not query or len(query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        results = search_similar_chunks(
            db=db,
            query=query,
            user_id=current_user.id,
            top_k=top_k,
            document_ids=document_ids
        )

        return {
            "query": query,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
