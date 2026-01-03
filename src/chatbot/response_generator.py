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
        lines.append(f"🤖 AFCON Assistant Response")
        lines.append("=" * 60)
        
        # Answer
        lines.append(f"\n{response.get('answer', 'No answer available')}\n")
        
        # Metadata
        if response.get("type"):
            lines.append(f"📌 Query Type: {response['type']}")
        
        if response.get("num_sources"):
            lines.append(f"📚 Sources Used: {response['num_sources']}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_match_summary(summary: Dict[str, Any]) -> str:
        """
        Format match summary for display
        
        Args:
            summary: Match summary dictionary
            
        Returns:
            Formatted match summary string
        """
        if "error" in summary:
            return f"❌ Error: {summary['error']}"
        
        lines = []
        status = summary.get("status", {})
        
        # Match header
        lines.append("\n⚽ MATCH SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Status: {status.get('status', 'Unknown')}")
        lines.append(f"Time: {status.get('time', 'N/A')}")
        
        # Scores
        lines.append("\n📊 SCORE:")
        for team in status.get("competitors", []):
            lines.append(f"  {team['team_name']}: {team['score']}")
        
        # Events
        events = summary.get("events", [])
        if events:
            lines.append("\n📝 KEY EVENTS:")
            for event in events[:10]:  # Show first 10 events
                if event['is_scoring']:
                    icon = "⚽"
                elif event['is_card']:
                    icon = "🟨"
                else:
                    icon = "•"
                
                players = ', '.join(event['participants'])
                lines.append(f"  {icon} {event['minute']} - {event['team']}: {players}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_sources(sources: List[Any]) -> str:
        """
        Format source documents
        
        Args:
            sources: List of source documents or dictionaries
            
        Returns:
            Formatted sources string
        """
        if not sources:
            return "No sources available"
        
        lines = ["\n📚 SOURCES:"]
        lines.append("=" * 60)
        
        for i, source in enumerate(sources, 1):
            if hasattr(source, 'page_content'):
                content = source.page_content
                metadata = source.metadata
            else:
                content = source.get('content', '')
                metadata = source.get('metadata', {})
            
            lines.append(f"\n[Source {i}]")
            lines.append(content[:200] + "..." if len(content) > 200 else content)
            
            if metadata.get('date'):
                lines.append(f"Date: {metadata['date']}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
