"""
Query dispatcher to route questions to appropriate handlers
"""
import re
from typing import Dict, Any, Literal
from langchain_groq import ChatGroq
from config import settings


QueryType = Literal["live", "historical", "statistics", "general"]


class QueryDispatcher:
    """Dispatch user queries to appropriate handlers (live data vs RAG)"""
    
    def __init__(self):
        """Initialize query dispatcher"""
        self.llm = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0
        )
        
        # Keywords for quick classification
        self.live_keywords = [
            "live", "current", "now", "ongoing", "today", "happening",
            "real-time", "latest score", "what's the score"
        ]
        
        self.historical_keywords = [
            "history", "past", "previous", "won", "winners", "champion",
            "all-time", "historical", "which team", "who has", "most wins"
        ]
        
        self.stats_keywords = [
            "statistics", "stats", "possession", "shots", "passes",
            "performance", "average", "total", "percentage"
        ]
    
    def classify_query(self, query: str) -> QueryType:
        """
        Classify query type using keyword matching and heuristics
        
        Args:
            query: User query string
            
        Returns:
            Query type classification
        """
        query_lower = query.lower()
        
        # Check for live match queries
        if any(keyword in query_lower for keyword in self.live_keywords):
            return "live"
        
        # Check for statistics queries
        if any(keyword in query_lower for keyword in self.stats_keywords):
            return "statistics"
        
        # Check for historical queries
        if any(keyword in query_lower for keyword in self.historical_keywords):
            return "historical"
        
        # Default to historical/RAG for most questions
        return "historical"
    
    def extract_team_name(self, query: str) -> str:
        """
        Extract team name from query if present
        
        Args:
            query: User query
            
        Returns:
            Team name or empty string
        """
        # Common AFCON teams
        teams = [
            "Morocco", "Egypt", "Senegal", "Algeria", "Tunisia", "Nigeria",
            "Cameroon", "Ghana", "Ivory Coast", "Mali", "Burkina Faso",
            "South Africa", "Comoros", "Tanzania", "Zambia", "Zimbabwe"
        ]
        
        for team in teams:
            if team.lower() in query.lower():
                return team
        
        return ""
    
    def should_use_live_data(self, query: str) -> bool:
        """
        Determine if query requires live data
        
        Args:
            query: User query
            
        Returns:
            True if live data needed
        """
        return self.classify_query(query) == "live"
    
    def get_routing_info(self, query: str) -> Dict[str, Any]:
        """
        Get complete routing information for a query
        
        Args:
            query: User query
            
        Returns:
            Dictionary with routing information
        """
        query_type = self.classify_query(query)
        team_name = self.extract_team_name(query)
        
        return {
            "query_type": query_type,
            "use_live_data": query_type == "live",
            "use_rag": query_type in ["historical", "statistics"],
            "team_name": team_name,
            "original_query": query
        }
