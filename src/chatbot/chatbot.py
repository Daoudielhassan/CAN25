"""
Main chatbot orchestrator integrating all components
"""
from typing import Dict, Any, Optional
from src.live_data import ESPNAPIClient, LiveMatchManager
from src.knowledge_base import VectorStoreManager
from src.rag import AFCONRetriever, AFCONConversationalRAG
from .dispatcher import QueryDispatcher
from config import settings


class AFCONChatbot:
    """Main chatbot class orchestrating live data and RAG"""
    
    def __init__(
        self, 
        live_event_id: Optional[str] = None,
        use_conversational: bool = True
    ):
        """
        Initialize AFCON chatbot
        
        Args:
            live_event_id: ESPN event ID for live match monitoring
            use_conversational: Use conversational RAG with history
        """
        # Initialize dispatcher
        self.dispatcher = QueryDispatcher()
        
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
        
        if use_conversational:
            self.rag_chain = AFCONConversationalRAG(self.retriever)
        else:
            from src.rag import AFCONRAGChain
            self.rag_chain = AFCONRAGChain(self.retriever)
    
    def _load_or_create_vectorstore(self):
        """Load existing vector store or notify to create one"""
        try:
            self.vectorstore_manager.load_vectorstore()
            print("✓ Loaded existing vector store")
        except FileNotFoundError:
            print("⚠️  No vector store found. Run setup script to create one.")
            print("   python scripts/setup_vectorstore.py")
    
    def chat(self, query: str) -> Dict[str, Any]:
        """
        Process a user query and return response
        
        Args:
            query: User's question or statement
            
        Returns:
            Response dictionary with answer and metadata
        """
        # Get routing information
        routing = self.dispatcher.get_routing_info(query)
        
        # Route to appropriate handler
        if routing["use_live_data"]:
            return self._handle_live_query(query, routing)
        else:
            return self._handle_rag_query(query, routing)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.rag_chain.get_cache_stats()
    
    def clear_cache(self):
        """Clear response cache"""
        self.rag_chain.clear_cache()
    
    def _handle_live_query(self, query: str, routing: Dict) -> Dict[str, Any]:
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
    
    def _handle_rag_query(self, query: str, routing: Dict) -> Dict[str, Any]:
        """Handle queries using RAG (historical/statistics)"""
        # Use RAG to answer - increased k for better context
        result = self.rag_chain.answer_question(query, k=8)
        
        return {
            "answer": result["answer"],
            "type": routing["query_type"],
            "sources": result.get("context_docs", []),
            "num_sources": result["num_sources"],
            "routing": routing
        }
    
    def _format_live_response(self, update: Dict, query: str) -> str:
        """Format live match data into natural language response"""
        parts = []
        
        # Match status
        parts.append(f"📍 Match Status: {update['status']} ({update['time']})")
        
        # Current score
        score_parts = [f"{team}: {score}" for team, score in update['score'].items()]
        parts.append(f"⚽ Score: {' - '.join(score_parts)}")
        
        # Recent goals
        if update['new_goals']:
            parts.append("\n🎯 Recent Goals:")
            for goal in update['new_goals']:
                players = ', '.join(goal['participants'])
                parts.append(f"  • {goal['minute']} - {goal['team']}: {players}")
        
        # Recent cards
        if update['new_cards']:
            parts.append("\n🟨 Recent Cards:")
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
        print(f"✓ Now monitoring match: {event_id}")
    
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
