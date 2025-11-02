from database import SessionLocal
from models import DocumentDB, DocumentChunkDB, UserDB
from retrieval import search_similar_chunks

db = SessionLocal()

# Check users
users = db.query(UserDB).all()
print("Users:")
for u in users:
    print(f"  ID: {u.id}, Email: {u.email}")

# Check documents and their owners
docs = db.query(DocumentDB).all()
print("\nDocuments:")
for d in docs:
    print(f"  ID: {d.id}, File: {d.original_filename}, User: {d.user_id}, Status: {d.processing_status}")

    # Count chunks with embeddings
    chunks_with_emb = db.query(DocumentChunkDB).filter(
        DocumentChunkDB.document_id == d.id,
        DocumentChunkDB.embedding.isnot(None)
    ).count()
    print(f"    Chunks with embeddings: {chunks_with_emb}")

# Test search with the correct user_id
print("\n--- Testing Search ---")
if users:
    test_user_id = users[0].id  # Use first user
    print(f"Searching as user_id: {test_user_id}")

    results = search_similar_chunks(
        db=db,
        query="What is Retrieval-Augmented Generation?",
        user_id=test_user_id,
        top_k=3
    )

    print(f"\nResults: {len(results)}")
    for r in results:
        print(f"  Similarity: {r['similarity']:.4f}")
        print(f"  Text: {r['text'][:100]}...")
        print()

db.close()
