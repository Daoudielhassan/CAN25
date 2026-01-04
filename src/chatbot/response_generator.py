"""
Response formatter for consistent output formatting
"""
from typing import Dict, Any, List
from datetime import datetime


class ResponseFormatter:
    """Format chatbot responses for different output channels"""
    
    @staticmethod
    def format_for_api(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format response for API output
        
        Args:
            response: Raw chatbot response
            
        Returns:
            Formatted API response
        """
        return {
            "answer": response.get("answer", ""),
            "type": response.get("type", "general"),
            "metadata": {
                "query_type": response.get("routing", {}).get("query_type"),
                "num_sources": response.get("num_sources", 0),
                "timestamp": datetime.now().isoformat()
            },
            "success": "error" not in response
        }
    
    @staticmethod
    def format_for_console(response: Dict[str, Any]) -> str:
        """
        Format response for console output
        
        Args:
            response: Raw chatbot response
            
        Returns:
            Formatted string for console
        """
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append(f" AFCON Assistant Response")
        lines.append("=" * 60)
        
        # Answer
        lines.append(f"\n{response.get('answer', 'No answer available')}\n")
        
        # Metadata
        if response.get("type"):
            lines.append(f" Query Type: {response['type']}")
        
        if response.get("num_sources"):
            lines.append(f"[BOOK] Sources Used: {response['num_sources']}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
