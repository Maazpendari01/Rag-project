from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, JSON, func
from sqlalchemy.orm import relationship
from database import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    todos = relationship("TodoDB", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("DocumentDB", back_populates="user", cascade="all, delete-orphan")


class TodoDB(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("UserDB", back_populates="todos")


class DocumentDB(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("UserDB", back_populates="documents")
    chunks = relationship("DocumentChunkDB", back_populates="document", cascade="all, delete-orphan")


class DocumentChunkDB(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=False)
    embedding = Column(JSON, nullable=True)  # Store embeddings as JSON array
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    document = relationship("DocumentDB", back_populates="chunks")


class ConversationDB(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, default="New Conversation")  # Auto-generated from first message
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("UserDB", backref="conversations")
    messages = relationship("MessageDB", back_populates="conversation", cascade="all, delete-orphan")


class MessageDB(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # Store which chunks were used
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    conversation = relationship("ConversationDB", back_populates="messages")
