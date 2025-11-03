from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import get_settings

# Get the settings object, which reads from the environment
settings = get_settings()

# Use the DATABASE_URL from your Render environment variables!
DATABASE_URL = settings.database_url

# Now, create the engine with the correct URL
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Create engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True = show SQL logs (helpful in dev)

# ✅ Create Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Base class for models
Base = declarative_base()


# ✅ Utility function to initialize (drop + create) all tables
def init_db():
    """
    Drops all existing tables and recreates them.
    Use only in development — this will ERASE all data.
    """
    from models import UserDB, TodoDB, DocumentDB, DocumentChunkDB  # Import all models

    print("🧹 Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("🧱 Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables recreated successfully!")


# ✅ Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
