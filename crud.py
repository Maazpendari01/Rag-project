from datetime import datetime
from typing import Dict, List
from sqlalchemy import func

from sqlalchemy.orm import Session

from auth import get_password_hash
from models import DocumentChunkDB, DocumentDB, TodoDB, UserDB,ConversationDB, MessageDB
from schemas import TodoCreate, TodoUpdate, UserCreate


# ------------------ TODO OPERATIONS ------------------
def get_all_todos(db: Session):
    return db.query(TodoDB).all()


def get_todo_by_id(db: Session, todo_id: int):
    return db.query(TodoDB).filter(TodoDB.id == todo_id).first()


def create_todo(db: Session, todo: TodoCreate):
    db_todo = TodoDB(title=todo.title)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


def update_todo(db: Session, todo_id: int, todo_update: TodoUpdate):  # type: ignore
    db_todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if db_todo:
        db_todo.title = todo_update.title  # type: ignore

        db_todo.completed = todo_update.completed  # type: ignore
        db.commit()
        db.refresh(db_todo)
    return db_todo


def complete_todo(db: Session, todo_id: int):  # type: ignore
    db_todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if db_todo:
        db_todo.completed = True  # type: ignore
        db.commit()
        db.refresh(db_todo)
    return db_todo


def delete_todo(db: Session, todo_id: int):
    db_todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if db_todo:
        db.delete(db_todo)
        db.commit()
        return True
    return False


# ------------------ USER OPERATIONS ------------------
def get_user_by_email(db: Session, email: str):
    return db.query(UserDB).filter(UserDB.email == email).first()


def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = UserDB(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ------------------ DOCUMENT OPERATIONS ------------------
def create_document(
    db: Session,
    filename: str,
    original_filename: str,
    file_path: str,
    file_size: int,
    content_type: str,
    user_id: int,
):
    document = DocumentDB(
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        content_type=content_type,
        user_id=user_id,
        uploaded_at=datetime.utcnow(),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_user_documents(db: Session, user_id: int):
    return db.query(DocumentDB).filter(DocumentDB.user_id == user_id).all()


def get_document_by_id(db: Session, document_id: int, user_id: int):
    return (
        db.query(DocumentDB)
        .filter(DocumentDB.id == document_id, DocumentDB.user_id == user_id)
        .first()
    )


def delete_document(db: Session, document_id: int, user_id: int):
    document = get_document_by_id(db, document_id, user_id)
    if document:
        db.delete(document)
        db.commit()
        return True
    return False


# ------------------ CHUNK OPERATIONS ------------------
def create_document_chunks(db: Session, document_id: int, chunks: List[Dict]):
    """Create document chunks with embeddings"""
    chunk_objects = []

    for chunk in chunks:
        chunk_obj = DocumentChunkDB(
            document_id=document_id,
            chunk_index=chunk["chunk_index"],
            text=chunk["text"],
            char_start=chunk["char_start"],
            char_end=chunk["char_end"],
            token_count=chunk["token_count"],
            embedding=chunk.get("embedding")  # This saves the embedding as JSON
        )
        chunk_objects.append(chunk_obj)

    db.add_all(chunk_objects)
    db.commit()

    return chunk_objects


def get_document_chunks(db: Session, document_id: int):
    return (
        db.query(DocumentChunkDB)
        .filter(DocumentChunkDB.document_id == document_id)
        .all()
    )


def delete_document_chunks(db: Session, document_id: int):
    """Delete all chunks related to a document"""
    db.query(DocumentChunkDB).filter(
        DocumentChunkDB.document_id == document_id
    ).delete()
    db.commit()

# Conversation operations
def create_conversation(db: Session, user_id: int, title: str = "New Conversation"):
    """Create a new conversation"""
    conversation = ConversationDB(
        user_id=user_id,
        title=title
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

def get_user_conversations(db: Session, user_id: int):
    """Get all conversations for a user"""
    conversations = db.query(ConversationDB).filter(
        ConversationDB.user_id == user_id
    ).order_by(ConversationDB.updated_at.desc()).all()

    # Add message count
    result = []
    for conv in conversations:
        conv_dict = {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "message_count": len(conv.messages)
        }
        result.append(conv_dict)

    return result

def get_conversation_by_id(db: Session, conversation_id: int, user_id: int):
    """Get a conversation with all messages"""
    conversation = db.query(ConversationDB).filter(
        ConversationDB.id == conversation_id,
        ConversationDB.user_id == user_id
    ).first()
    return conversation

def delete_conversation(db: Session, conversation_id: int, user_id: int):
    """Delete a conversation and all its messages"""
    conversation = db.query(ConversationDB).filter(
        ConversationDB.id == conversation_id,
        ConversationDB.user_id == user_id
    ).first()

    if conversation:
        db.delete(conversation)
        db.commit()
        return True
    return False

# Message operations
def create_message(db: Session, conversation_id: int, role: str, content: str, sources: List[Dict] = None):
    """Add a message to a conversation"""
    message = MessageDB(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=sources
    )
    db.add(message)

    # Update conversation timestamp
    conversation = db.query(ConversationDB).filter(
        ConversationDB.id == conversation_id
    ).first()
    if conversation:
        conversation.updated_at = func.now()

    db.commit()
    db.refresh(message)
    return message

def get_conversation_messages(db: Session, conversation_id: int, limit: int = 10):
    """Get recent messages from a conversation"""
    messages = db.query(MessageDB).filter(
        MessageDB.conversation_id == conversation_id
    ).order_by(MessageDB.created_at.desc()).limit(limit).all()

    # Return in chronological order
    return list(reversed(messages))
