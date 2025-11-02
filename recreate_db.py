from database import Base, engine

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)

print("Creating all tables...")
Base.metadata.create_all(bind=engine)

print("Done! Database recreated.")
print("\nTables created:")
print("- users")
print("- todos")
print("- documents")
print("- document_chunks (with JSON embedding column)")
