"""
Vector store manager using FAISS for embedding storage and retrieval
"""
import pickle
from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import settings


class VectorStoreManager:
    """Manage FAISS vector store for AFCON knowledge base"""
    
    def __init__(self, store_path: Optional[str] = None):
        """
        Initialize vector store manager
        
        Args:
            store_path: Path to save/load vector store
        """
        self.store_path = Path(store_path or settings.vector_store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings - Using free local HuggingFace embeddings
        print("🔄 Loading embedding model (first time may take a moment)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.vectorstore: Optional[FAISS] = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Increased from 500 for more context
            chunk_overlap=100,  # Increased from 50 for better continuity
            separators=[" | ", "\n\n", "\n", " ", ""]
        )
    
    def create_vectorstore(self, documents: List[Document]) -> FAISS:
        """
        Create vector store from documents
        
        Args:
            documents: List of documents to embed
            
        Returns:
            FAISS vector store
        """
        if not documents:
            raise ValueError("No documents provided")
        
        print(f"🔄 Creating embeddings for {len(documents)} documents...")
        
        # Split documents if needed
        split_docs = self.text_splitter.split_documents(documents)
        print(f"📝 Split into {len(split_docs)} chunks")
        
        # Create vector store
        self.vectorstore = FAISS.from_documents(
            documents=split_docs,
            embedding=self.embeddings
        )
        
        print("✓ Vector store created successfully")
        return self.vectorstore
    
    def save_vectorstore(self, name: str = "afcon_vectorstore"):
        """
        Save vector store to disk
        
        Args:
            name: Name for the saved vector store
        """
        if not self.vectorstore:
            raise ValueError("No vector store to save")
        
        save_path = self.store_path / name
        self.vectorstore.save_local(str(save_path))
        print(f"💾 Vector store saved to {save_path}")
    
    def load_vectorstore(self, name: str = "afcon_vectorstore") -> FAISS:
        """
        Load vector store from disk
        
        Args:
            name: Name of the saved vector store
            
        Returns:
            Loaded FAISS vector store
        """
        load_path = self.store_path / name
        
        if not load_path.exists():
            raise FileNotFoundError(f"Vector store not found at {load_path}")
        
        self.vectorstore = FAISS.load_local(
            str(load_path),
            embeddings=self.embeddings,
            allow_dangerous_deserialization=True
        )
        
        print(f"📂 Vector store loaded from {load_path}")
        return self.vectorstore
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[dict] = None
    ) -> List[Document]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Metadata filters
            
        Returns:
            List of similar documents
        """
        if not self.vectorstore:
            raise ValueError("No vector store loaded")
        
        if filter_dict:
            return self.vectorstore.similarity_search(
                query, 
                k=k,
                filter=filter_dict
            )
        else:
            return self.vectorstore.similarity_search(query, k=k)
    
    def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 5
    ) -> List[tuple[Document, float]]:
        """
        Search for similar documents with relevance scores
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (document, score) tuples
        """
        if not self.vectorstore:
            raise ValueError("No vector store loaded")
        
        return self.vectorstore.similarity_search_with_score(query, k=k)
    
    def add_documents(self, documents: List[Document]):
        """
        Add new documents to existing vector store
        
        Args:
            documents: Documents to add
        """
        if not self.vectorstore:
            raise ValueError("No vector store loaded. Create one first.")
        
        split_docs = self.text_splitter.split_documents(documents)
        self.vectorstore.add_documents(split_docs)
        print(f"➕ Added {len(split_docs)} new document chunks")
    
    def get_retriever(self, k: int = 5, **kwargs):
        """
        Get a retriever interface for the vector store
        
        Args:
            k: Number of documents to retrieve
            **kwargs: Additional retriever arguments
            
        Returns:
            LangChain retriever
        """
        if not self.vectorstore:
            raise ValueError("No vector store loaded")
        
        return self.vectorstore.as_retriever(
            search_kwargs={"k": k, **kwargs}
        )
