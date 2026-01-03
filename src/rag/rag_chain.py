"""
RAG Chain implementation for AFCON chatbot
"""
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from .retriever import AFCONRetriever
from config import settings
from ..chatbot.cache import ResponseCache
from ..chatbot.redis_cache import RedisCache


class AFCONRAGChain:
    """RAG chain for answering AFCON questions with context"""
    
    def __init__(self, retriever: AFCONRetriever):
        """
        Initialize RAG chain
        
        Args:
            retriever: AFCON retriever instance
        """
        self.retriever = retriever
        
        # Initialize Redis cache for RAG answers (1 hour TTL)
        self.redis_cache = RedisCache()
        
        # Keep file cache as fallback
        self.cache = ResponseCache(ttl=86400)
        
        # Initialize LLM - Using Groq
        self.llm = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.1,
            max_tokens=200  # Increased to allow complete responses
        )
        
        # Create prompt template
        self.prompt = self._create_prompt_template()
        
        # Create chain using LCEL
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create the RAG prompt template"""
        template = """Answer the question using the context below. Be direct and factual.

Context:
{context}

Question: {question}

Rules:
- Answer directly with facts from the context
- Include specific details: team names, scores, dates, player names
- Use **bold** for emphasis on teams/players
- Keep it concise: 1-3 sentences maximum
- NEVER say: "we were discussing", "I mentioned", "according to the database", "I should note"
- NEVER reference previous conversations or what you said before
- Just answer the question directly

Answer:"""
        
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def answer_question(
        self, 
        question: str, 
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG with multi-level caching
        
        Args:
            question: User's question
            k: Number of context documents to retrieve
            
        Returns:
            Dictionary with answer and metadata
        """
        # Level 1: Check Redis cache first (fast, shared)
        if self.redis_cache.enabled:
            cached_answer = self.redis_cache.get_rag_answer(question)
            if cached_answer:
                docs = self.retriever.retrieve(question, k=k)  # Light operation for metadata
                return {
                    "answer": cached_answer,
                    "context_docs": docs,
                    "num_sources": k,
                    "cached": True,
                    "cache_type": "redis"
                }
        
        # Level 2: Check file cache (fallback)
        cached_response = self.cache.get(question)
        if cached_response:
            docs = self.retriever.retrieve(question, k=k)
            return {
                "answer": cached_response['answer'],
                "context_docs": docs,
                "num_sources": len(cached_response['sources']),
                "cached": True,
                "cache_type": f"file ({cached_response['cache_type']})"
            }
        
        # Level 3: Generate new answer (uses API quota)
        print(f"🔄 Generating new answer (uses API quota)...")
        
        # Retrieve relevant context
        docs = self.retriever.retrieve(question, k=k)
        
        # Format context
        context = self.retriever.format_retrieved_context(docs)
        
        # Generate answer (uses API quota)
        response = self.chain.invoke({
            "context": context,
            "question": question
        })
        
        # Cache the response in both levels
        sources = [doc.metadata.get('source', 'unknown') for doc in docs]
        
        # Redis cache (1 hour TTL)
        if self.redis_cache.enabled:
            self.redis_cache.set_rag_answer(question, response, sources)
        
        # File cache (24 hour TTL as backup)
        self.cache.set(question, response, sources)
        
        return {
            "answer": response,
            "context_docs": docs,
            "num_sources": len(docs),
            "cached": False
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics from all levels"""
        stats = {
            "file_cache": self.cache.get_stats()
        }
        
        if self.redis_cache.enabled:
            stats["redis_cache"] = self.redis_cache.get_stats()
        
        return stats
    
    def clear_cache(self):
        """Clear response cache at all levels"""
        self.cache.clear()
        if self.redis_cache.enabled:
            self.redis_cache.invalidate_pattern(f"{self.redis_cache.prefix}:rag:*")
    
    def answer_with_sources(
        self, 
        question: str, 
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Answer question and include source information
        
        Args:
            question: User's question
            k: Number of context documents to retrieve
            
        Returns:
            Dictionary with answer, sources, and scores
        """
        # Retrieve with scores
        docs_with_scores = self.retriever.retrieve_with_scores(question, k=k)
        
        # Extract docs
        docs = [doc for doc, score in docs_with_scores]
        
        # Format context
        context = self.retriever.format_retrieved_context(docs)
        
        # Generate answer
        response = self.chain.invoke({
            "context": context,
            "question": question
        })
        
        # Format sources with scores
        sources = []
        for doc, score in docs_with_scores:
            sources.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(score)
            })
        
        return {
            "answer": response,
            "sources": sources,
            "num_sources": len(sources)
        }


class AFCONConversationalRAG(AFCONRAGChain):
    """Extended RAG chain with conversation history support"""
    
    def __init__(self, retriever: AFCONRetriever):
        super().__init__(retriever)
        self.conversation_history = []
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create conversational RAG prompt template"""
        template = """You are an expert AFCON (African Cup of Nations) assistant having a conversation with a user.

Conversation History:
{history}

Context from AFCON database:
{context}

Current Question: {question}

Instructions:
- Consider the conversation history for context
- Provide accurate answers based on the database context
- Be conversational and maintain context from previous exchanges
- If referring to previous questions, make it clear
- Include relevant statistics and details

Answer:"""
        
        return PromptTemplate(
            template=template,
            input_variables=["history", "context", "question"]
        )
    
    def answer_question(
        self, 
        question: str, 
        k: int = 5
    ) -> Dict[str, Any]:
        """Answer with conversation history"""
        # Retrieve context
        docs = self.retriever.retrieve(question, k=k)
        context = self.retriever.format_retrieved_context(docs)
        
        # Format history
        history = self._format_history()
        
        # Generate answer
        response = self.chain.invoke({
            "history": history,
            "context": context,
            "question": question
        })
        
        # Update history
        self.conversation_history.append({
            "question": question,
            "answer": response
        })
        
        # Keep last 5 exchanges
        if len(self.conversation_history) > 5:
            self.conversation_history = self.conversation_history[-5:]
        
        return {
            "answer": response,
            "context_docs": docs,
            "num_sources": len(docs)
        }
    
    def _format_history(self) -> str:
        """Format conversation history"""
        if not self.conversation_history:
            return "No previous conversation."
        
        history_parts = []
        for exchange in self.conversation_history:
            history_parts.append(f"User: {exchange['question']}")
            history_parts.append(f"Assistant: {exchange['answer']}")
        
        return "\n".join(history_parts)
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
