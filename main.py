from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
# Make sure all your models are imported here so they are created
from models import ConversationDB, MessageDB, Base
from routers import chat, documents, todos, users

# Create database tables
# This line should be here to ensure tables are created on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG API", version="1.0.0")

# ✅ --- THIS IS THE UPDATED FIX ---
# We create a list of all "allowed" websites.

origins = [
    "https://rag-chatbot-tau-five.vercel.app",  # Your LIVE Vercel frontend
    "http://localhost:5173",                  # Your local Vite dev server
    "http://localhost:3000",                  # Common local React dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,   # Use the list of origins
    allow_credentials=True,
    allow_methods=["*"],     # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],     # Allow all headers (like "Authorization")
)
# --- END OF FIX ---


# ✅ Include routers
# This setup assumes your /auth routes are inside users.router
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
