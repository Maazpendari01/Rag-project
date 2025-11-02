from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr, Field


# Todo schemas
class TodoCreate(BaseModel):
    title: str


class TodoUpdate(BaseModel):
    title: str
    completed: bool


class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool

    class Config:
        from_attributes = True


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


# Document schemas
class DocumentUpload(BaseModel):
    pass


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    uploaded_at: datetime
    processing_status: str
    processing_error: Optional[str] = None
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChunkResponse(BaseModel):
    id: int
    chunk_index: int
    text: str
    char_start: int
    char_end: int
    token_count: int

    class Config:
        from_attributes = True


class DocumentWithChunks(DocumentResponse):
    chunks: List[ChunkResponse] = []


class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 1024
    model: str = "llama-3.1-70b-versatile"
    conversation_id: Optional[int] = None # Add this line


class ChatResponse(BaseModel):
    response: str
    model: str
    sources: List[Dict] = []  # Add this line
    conversation_id: Optional[int] = None  # Add this line
# Message schemas
class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[List[Dict]] = []
    created_at: datetime

    class Config:
        from_attributes = True

# Conversation schemas
class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime]
    message_count: int = 0

    class Config:
        from_attributes = True

class ConversationWithMessages(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: List[MessageResponse]

    class Config:
        from_attributes = True

# Chat with conversation
class ConversationChatRequest(BaseModel):
    conversation_id: Optional[int] = None  # If None, create new conversation
    message: str
    max_tokens: int = 1024
    model: str = "llama-3.1-8b-instant"
    # --- THIS IS THE NEW LINE ---
    document_ids: List[int] = [] # Optional list of doc IDs to filter search
