from embeddings import generate_embedding, generate_query_embedding

print("Testing embeddings...")

# Test document embedding
text = "FastAPI is a modern Python web framework for building APIs"
doc_embedding = generate_embedding(text)

print(f"\nDocument text: {text}")
print(f"Embedding length: {len(doc_embedding)}")
print(f"First 10 values: {doc_embedding[:10]}")

# Test query embedding
query = "How do I use FastAPI?"
query_embedding = generate_query_embedding(query)

print(f"\nQuery: {query}")
print(f"Query embedding length: {len(query_embedding)}")
print(f"First 10 values: {query_embedding[:10]}")

print("\n✅ Embeddings working!")
