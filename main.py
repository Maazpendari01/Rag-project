from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from models import Base, ConversationDB, MessageDB
from routers import chat, documents, todos, users

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG API", version="1.0.0")

# ✅ Add CORS middleware BEFORE including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rag-chatbot-tau-five.vercel.app"],   # React frontend
    allow_credentials=True,
    allow_methods=["*"],  # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # allow all custom headers like "Content-Type"
)

# ✅ Include routers - users.router should have /auth routes
app.include_router(users.router)  # This should have /auth/register and /auth/login
app.include_router(todos.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/")
def read_root():
    return {"message": "RAG API Running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
