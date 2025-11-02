import pdfplumber
import docx
from typing import List, Dict
import re
import asyncio
from datetime import datetime

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise Exception(f"Error extracting PDF: {str(e)}")

    return text.strip()

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from Word document"""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting DOCX: {str(e)}")

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from plain text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        raise Exception(f"Error reading TXT: {str(e)}")

def extract_text(file_path: str, content_type: str) -> str:
    """Route to appropriate extraction method based on file type"""
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_path)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_path)
    elif content_type == "text/plain":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {content_type}")

def estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters)"""
    return len(text) // 4

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Dict]:
    """Split text into overlapping chunks"""
    chunks = []

    if not text or len(text) == 0:
        return chunks

    if len(text) <= chunk_size:
        return [{
            "text": text,
            "char_start": 0,
            "char_end": len(text),
            "chunk_index": 0,
            "token_count": estimate_tokens(text)
        }]

    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            search_start = end - int(chunk_size * 0.2)
            last_period = text.rfind('.', search_start, end)
            last_exclaim = text.rfind('!', search_start, end)
            last_question = text.rfind('?', search_start, end)
            sentence_end = max(last_period, last_exclaim, last_question)

            if sentence_end != -1 and sentence_end > search_start:
                end = sentence_end + 1

        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "char_start": start,
                "char_end": end,
                "chunk_index": chunk_index,
                "token_count": estimate_tokens(chunk_text)
            })
            chunk_index += 1

        start = end - chunk_overlap

        if start >= len(text):
            break

    return chunks

def clean_text(text: str) -> str:
    """Clean extracted text"""
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    return text.strip()

async def process_document_async(
    document_id: int,
    file_path: str,
    content_type: str,
    db_session_maker
):
    """Process document in background - now with embeddings"""
    from crud import create_document_chunks
    from models import DocumentDB
    from embeddings import generate_embeddings_batch  # NEW IMPORT

    db = db_session_maker()

    try:
        document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if not document:
            raise Exception("Document not found")

        # Update status to processing
        document.processing_status = "processing"
        db.commit()

        print(f"[Document {document_id}] Extracting text...")
        raw_text = extract_text(file_path, content_type)

        await asyncio.sleep(1)  # Simulate processing delay

        print(f"[Document {document_id}] Cleaning text...")
        cleaned_text = clean_text(raw_text)

        print(f"[Document {document_id}] Chunking text...")
        chunks = chunk_text(cleaned_text, chunk_size=1000, chunk_overlap=200)

        # NEW: Generate embeddings for all chunks
        print(f"[Document {document_id}] Generating embeddings for {len(chunks)} chunks...")
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = generate_embeddings_batch(chunk_texts)

        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i]

        print(f"[Document {document_id}] Saving chunks to database...")
        create_document_chunks(db, document_id, chunks)

        # Mark as completed
        document.processing_status = "completed"
        document.processed_at = datetime.utcnow()
        db.commit()

        print(f"[Document {document_id}] ✅ Processing complete! {len(chunks)} chunks with embeddings created.")

    except Exception as e:
        print(f"[Document {document_id}] ❌ Error: {str(e)}")
        document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if document:
            document.processing_status = "failed"
            document.processing_error = str(e)
            db.commit()

    finally:
        db.close()
