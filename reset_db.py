from database import Base, engine
from models import *  # noqa: F403

print("Dropping existing tables...")
Base.metadata.drop_all(bind=engine)

print("Creating new tables...")
Base.metadata.create_all(bind=engine)

print("✅ Database reset complete! Tables are now up to date.")
