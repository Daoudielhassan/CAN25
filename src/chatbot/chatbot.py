"""
Main chatbot orchestrator integrating all components
"""
from typing import Dict, Any, Optional, List
from src.live_data import ESPNAPIClient, LiveMatchManager
from src.knowledge_base import VectorStoreManager
from src.rag import AFCONRetriever
from .dispatcher import QueryDispatcher
from .semantic_router import SemanticRouter
from config import settings


class AFCONChatbot:
    """Main chatbot class orchestrating live data and RAG"""
    
    def __init__(
        self, 
        live_event_id: Optional[str] = None,
        use_conversational: bool = True,
        use_semantic_routing: bool = True,
        use_agentic_rag: bool = False
    ):
        """
        Initialize AFCON chatbot
        
        Args:
            live_event_id: ESPN event ID for live match monitoring
            use_conversational: Use conversational RAG with history
            use_semantic_routing: Use semantic routing (embedding-based) instead of keyword matching
            use_agentic_rag: Use agentic RAG (LLM as agent with tools) for advanced reasoning
        """
        # Initialize routing - semantic or keyword-based
        self.use_semantic_routing = use_semantic_routing
        self.use_agentic_rag = use_agentic_rag
        
        if use_semantic_routing:
            self.semantic_router = SemanticRouter()
            self.dispatcher = None
        else:
            self.dispatcher = QueryDispatcher()
            self.semantic_router = None
        
        # Initialize live data components
        self.api_client = ESPNAPIClient()
        self.live_manager = None
        if live_event_id:
            self.live_manager = LiveMatchManager(
                event_id=live_event_id,
                refresh_interval=settings.refresh_interval
            )
        
        # Initialize RAG components
        self.vectorstore_manager = VectorStoreManager()
        self._load_or_create_vectorstore()
        
        self.retriever = AFCONRetriever(self.vectorstore_manager)
        
        # Choose RAG implementation - import here to avoid circular imports
        if use_agentic_rag:
            # Use agentic RAG with tool-calling agent
            from src.rag.agentic_rag import AgenticRAGChain
            self.rag_chain = AgenticRAGChain(self.retriever, self.api_client)
        elif use_conversational:
            # Use conversational RAG with history
            from src.rag.rag_chain import AFCONConversationalRAG
            self.rag_chain = AFCONConversationalRAG(self.retriever)
        else:
            # Use basic RAG
            from src.rag.rag_chain import AFCONRAGChain
            self.rag_chain = AFCONRAGChain(self.retriever)
    
    def _load_or_create_vectorstore(self):
        """Load existing vector store or notify to create one"""
        try:
            self.vectorstore_manager.load_vectorstore()
            print("[OK] Loaded existing vector store")
        except FileNotFoundError:
            print("[WARNING] No vector store found. Run setup script to create one.")
            print("   python scripts/setup_vectorstore.py")
    
    def chat(self, query: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Process a user query and return response
        
        Args:
            query: User's question or statement
            conversation_history: Previous conversation messages (list of {role, content})
            
        Returns:
            Response dictionary with answer and metadata
        """
        # Check if this is a follow-up question with references
        query_lower = query.lower()
        reference_words = ["the second", "the third", "the first", "that match", "that team", 
                          "those players", "this match", "this team", "it", "them", "that one",
                          "the one", "that game", "this game"]
        is_followup = any(ref in query_lower for ref in reference_words)
        
        # If it's a follow-up question with conversation history, always use RAG
        if is_followup and conversation_history and len(conversation_history) > 0:
            routing = {
                "use_rag": True,
                "use_live_api": False,
                "use_live_data": False,
                "query_type": "follow_up",
                "confidence": 0.95
            }
            return self._handle_rag_query(query, routing, conversation_history)
        
        # Get routing information using semantic router or dispatcher
        if self.use_semantic_routing:
            routing = self.semantic_router.classify_query(query)
        else:
            routing = self.dispatcher.get_routing_info(query)
        
        # Route to appropriate handler
        if routing.get("use_live_api", False) or routing.get("use_live_data", False):
            return self._handle_live_query(query, routing, conversation_history)
        elif routing.get("use_rag", False):
            return self._handle_rag_query(query, routing, conversation_history)
        else:
            # General queries
            return self._handle_general_query(query, routing, conversation_history)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.rag_chain.get_cache_stats()
    
    def clear_cache(self):
        """Clear response cache"""
        self.rag_chain.clear_cache()
    
    def _handle_live_query(self, query: str, routing: Dict, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Handle queries requiring live data"""
        if not self.live_manager:
            return {
                "answer": "No live match is currently being monitored. Please provide an event ID.",
                "type": "error",
                "routing": routing
            }
        
        # Fetch latest live data
        update = self.live_manager.fetch_update()
        
        if "error" in update:
            return {
                "answer": f"Error fetching live data: {update['error']}",
                "type": "error",
                "routing": routing
            }
        
        # Format live response
        answer = self._format_live_response(update, query)
        
        return {
            "answer": answer,
            "type": "live",
            "live_data": update,
            "routing": routing
        }
    
    def _handle_rag_query(self, query: str, routing: Dict, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Handle queries using RAG (historical/statistics)"""
        # Use RAG to answer - increased k for better context
        result = self.rag_chain.answer_question(query, k=8, conversation_history=conversation_history)
        
        return {
            "answer": result["answer"],
            "type": routing.get("query_type", "historical"),
            "sources": result.get("context_docs", []),
            "num_sources": result["num_sources"],
            "routing": routing,
            "confidence": routing.get("confidence", None)
        }
    
    def _handle_general_query(self, query: str, routing: Dict, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Handle general queries (greetings, help, etc)"""
        query_lower = query.lower()
        
        # Greeting responses
        if any(word in query_lower for word in ["hello", "hi", "hey", "bonjour"]):
            answer = "Welcome to AFCON 2025 Assistant! I can help you with match results, team statistics, group standings, and the latest tournament news. What would you like to know?"
        
        # Help requests
        elif any(word in query_lower for word in ["help", "what can you", "how do", "aide"]):
            answer = """I can help you with:
- Match results and statistics
- Group standings and qualified teams
- Latest AFCON news and updates
- Live match scores (when available)

Just ask your question naturally!"""
        
        # Default fallback - use RAG
        else:
            return self._handle_rag_query(query, routing, conversation_history)
        
        return {
            "answer": answer,
            "type": "general",
            "routing": routing,
            "confidence": routing.get("confidence", None)
        }
    
    def _format_live_response(self, update: Dict, query: str) -> str:
        """Format live match data into natural language response"""
        parts = []
        
        # Match status
        parts.append(f"[LIVE] Match Status: {update['status']} ({update['time']})")
        
        # Current score
        score_parts = [f"{team}: {score}" for team, score in update['score'].items()]
        parts.append(f"Score: {' - '.join(score_parts)}")
        
        # Recent goals
        if update['new_goals']:
            parts.append("\nRecent Goals:")
            for goal in update['new_goals']:
                players = ', '.join(goal['participants'])
                parts.append(f"  • {goal['minute']} - {goal['team']}: {players}")
        
        # Recent cards
        if update['new_cards']:
            parts.append("\nRecent Cards:")
            for card in update['new_cards']:
                players = ', '.join(card['participants'])
                parts.append(f"  • {goal['minute']} - {goal['team']}: {players}")
        
        return "\n".join(parts)
    
    def set_live_match(self, event_id: str):
        """
        Set or change the live match being monitored
        
        Args:
            event_id: ESPN event ID
        """
        self.live_manager = LiveMatchManager(
            event_id=event_id,
            refresh_interval=settings.refresh_interval
        )
        print(f"[OK] Now monitoring match: {event_id}")
    
    def get_match_summary(self, event_id: str) -> Dict[str, Any]:
        """
        Get comprehensive summary of a specific match
        
        Args:
            event_id: ESPN event ID
            
        Returns:
            Match summary dictionary
        """
        data = self.api_client.fetch_match_summary(event_id)
        
        if not data:
            return {"error": "Failed to fetch match data"}
        
        status = self.api_client.get_live_match_status(event_id)
        events = self.api_client.get_match_events(event_id)
        
        return {
            "status": status,
            "events": events,
            "raw_data": data
        }
    
    def clear_conversation(self):
        """Clear conversation history if using conversational mode"""
        if hasattr(self.rag_chain, 'clear_history'):
            self.rag_chain.clear_history()
            return {"message": "Conversation history cleared"}
        return {"message": "Not using conversational mode"}
    
    def explain_routing(self, query: str) -> str:
        """
        Explain how the query would be routed (debugging tool)
        
        Args:
            query: User query
            
        Returns:
            Human-readable explanation of routing decision
        """
        if self.use_semantic_routing:
            return self.semantic_router.explain_routing(query)
        else:
            routing = self.dispatcher.get_routing_info(query)
            explanation = f"Query: '{query}'\n\n"
            explanation += f"Query Type: {routing['query_type']}\n"
            explanation += f"Use Live Data: {routing['use_live_data']}\n"
            explanation += f"Use RAG: {routing['use_rag']}\n"
            if routing['team_name']:
                explanation += f"Detected Team: {routing['team_name']}\n"
            return explanation
    
    def get_routing_info(self) -> Dict[str, Any]:
        """Get information about the current routing configuration"""
        return {
            "routing_type": "semantic" if self.use_semantic_routing else "keyword",
            "semantic_routing_enabled": self.use_semantic_routing,
            "agentic_rag_enabled": self.use_agentic_rag,
            "live_match_monitoring": self.live_manager is not None,
            "conversational_mode": hasattr(self.rag_chain, 'clear_history')
        }
