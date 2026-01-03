"""
Retriever module for fetching relevant context from vector store
"""
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
# FIX: Import from 'langchain_classic.retrievers', NOT 'langchain_community'
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import LLMChainExtractor

from langchain_groq import ChatGroq
from src.knowledge_base.vector_store import VectorStoreManager
from config import settings


class AFCONRetriever:
    """Enhanced retriever for AFCON knowledge base"""
    
    def __init__(self, vectorstore_manager: VectorStoreManager):
        """
        Initialize retriever
        
        Args:
            vectorstore_manager: Vector store manager instance
        """
        self.vectorstore_manager = vectorstore_manager
        self.base_retriever = vectorstore_manager.get_retriever(k=5)
        
        # LLM for compression (optional)
        self.llm = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0
        )
    
    def retrieve(
        self, 
        query: str, 
        k: int = 5,
        filter_type: Optional[str] = None
    ) -> List[Document]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User query
            k: Number of documents to retrieve
            filter_type: Filter by document type (match, team, goal)
            
        Returns:
            List of relevant documents
        """
        # Build filter if specified
        filter_dict = None
        if filter_type:
            filter_dict = {"type": filter_type}
        
        # Perform similarity search
        docs = self.vectorstore_manager.similarity_search(
            query=query,
            k=k,
            filter_dict=filter_dict
        )
        
        return docs
    
    def retrieve_with_scores(
        self, 
        query: str, 
        k: int = 5
    ) -> List[tuple[Document, float]]:
        """
        Retrieve documents with relevance scores
        
        Args:
            query: User query
            k: Number of documents to retrieve
            
        Returns:
            List of (document, score) tuples
        """
        return self.vectorstore_manager.similarity_search_with_score(
            query=query,
            k=k
        )
    
    def get_compressed_retriever(self, k: int = 5):
        """
        Get a contextual compression retriever that extracts only relevant parts
        
        Args:
            k: Number of documents to retrieve
            
        Returns:
            Compression retriever
        """
        compressor = LLMChainExtractor.from_llm(self.llm)
        
        base_retriever = self.vectorstore_manager.get_retriever(k=k)
        
        return ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=base_retriever
        )
    
    def format_retrieved_context(self, docs: List[Document]) -> str:
        """
        Format retrieved documents into context string
        
        Args:
            docs: Retrieved documents
            
        Returns:
            Formatted context string
        """
        if not docs:
            return "No relevant information found."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"[Source {i}]")
            context_parts.append(doc.page_content)
            
            # Add metadata if useful
            if doc.metadata.get('date'):
                context_parts.append(f"Date: {doc.metadata['date']}")
            
            context_parts.append("")  # Empty line between sources
        
        return "\n".join(context_parts)
