"""
Response formatter for better chatbot outputs
"""
import re
from typing import Dict, Any


class ResponseFormatter:
    """Format chatbot responses for better readability"""
    
    @staticmethod
    def format_match_result(match_info: Dict[str, Any]) -> str:
        """Format match result in a clean way"""
        team1 = match_info.get('team1', 'Team 1')
        team2 = match_info.get('team2', 'Team 2')
        score1 = match_info.get('score1', 0)
        score2 = match_info.get('score2', 0)
        
        return f"**{team1} {score1} - {score2} {team2}**"
    
    @staticmethod
    def format_goal(goal_info: Dict[str, Any]) -> str:
        """Format goal information"""
        scorer = goal_info.get('scorer', 'Unknown')
        minute = goal_info.get('minute', '?')
        assister = goal_info.get('assister')
        
        formatted = f"⚽ **{scorer}** ({minute}')"
        if assister:
            formatted += f" - Assisted by {assister}"
        
        return formatted
    
    @staticmethod
    def format_stat(label: str, value: Any, unit: str = "") -> str:
        """Format a statistic"""
        return f"• **{label}**: {value}{unit}"
    
    @staticmethod
    def format_table(headers: list, rows: list) -> str:
        """Format data as markdown table"""
        table = "| " + " | ".join(headers) + " |\n"
        table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        
        for row in rows:
            table += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        
        return table
    
    @staticmethod
    def add_section(title: str, content: str) -> str:
        """Add a formatted section"""
        return f"\n### {title}\n\n{content}\n"
    
    @staticmethod
    def format_list(items: list, ordered: bool = False) -> str:
        """Format a list of items"""
        formatted = []
        for i, item in enumerate(items, 1):
            prefix = f"{i}. " if ordered else "• "
            formatted.append(f"{prefix}{item}")
        return "\n".join(formatted)
    
    @staticmethod
    def emphasize(text: str) -> str:
        """Add emphasis to text"""
        return f"**{text}**"
    
    @staticmethod
    def add_emoji_context(response: str, context_type: str) -> str:
        """Add contextual emojis to response"""
        emojis = {
            'match': '⚽',
            'goal': '🎯',
            'win': '🏆',
            'loss': '😔',
            'stats': '📊',
            'team': '👥',
            'player': '🧑‍⚽',
            'time': '⏱️',
            'trophy': '🏆'
        }
        
        emoji = emojis.get(context_type, '⚽')
        return f"{emoji} {response}"


# Example usage
if __name__ == "__main__":
    formatter = ResponseFormatter()
    
    # Test match result
    match = {'team1': 'Morocco', 'team2': 'Comoros', 'score1': 2, 'score2': 0}
    print(formatter.format_match_result(match))
    
    # Test goal
    goal = {'scorer': 'Brahim Díaz', 'minute': 55, 'assister': 'Noussair Mazraoui'}
    print(formatter.format_goal(goal))
    
    # Test stats
    print(formatter.format_stat('Possession', 65, '%'))
    print(formatter.format_stat('Shots on Target', 7))
