"""
Quick script to verify vector store content
"""
from src.knowledge_base import VectorStoreManager
from pathlib import Path

# Initialize vector store manager
manager = VectorStoreManager()

# Load vector store
try:
    vectorstore = manager.load_vectorstore()
    
    print("=" * 60)
    print("Vector Store Information")
    print("=" * 60)
    print()
    
    # Get all documents
    if hasattr(vectorstore, 'docstore'):
        num_docs = len(vectorstore.docstore._dict)
        print(f"📊 Total documents in vector store: {num_docs}")
        print()
        
        # Sample some documents
        print("Sample documents:")
        print("-" * 60)
        for i, (doc_id, doc) in enumerate(list(vectorstore.docstore._dict.items())[:5]):
            print(f"\n{i+1}. Type: {doc.metadata.get('type', 'unknown')}")
            print(f"   Content: {doc.page_content[:150]}...")
            if doc.metadata.get('type') == 'match_summary':
                print(f"   ✅ Match summary found!")
    else:
        print("Could not access document store details")
    
    print("\n" + "=" * 60)
    
    # Test a specific query
    print("\nTesting query: 'Algeria match results'")
    print("-" * 60)
    docs = manager.similarity_search("Algeria match results wins losses", k=5)
    
    for i, doc in enumerate(docs, 1):
        print(f"\n{i}. Type: {doc.metadata.get('type')}")
        print(f"   Source: {doc.metadata.get('source')}")
        print(f"   Content: {doc.page_content[:200]}...")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
