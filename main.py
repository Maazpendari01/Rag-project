from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models import ConversationDB, MessageDB, Base
from routers import chat, documents, todos, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG API", version="1.0.0")

origins = [
    "https://rag-chatbot-tau-five.vercel.app",  # your Vercel frontend
    "https://rag-backend.onrender.com",    # your backend
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(todos.router)
app.include_router(documents.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "RAG API Running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
