"""
Live match data manager for monitoring and storing match events
"""
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
from .api_client import ESPNAPIClient


class LiveMatchManager:
    """Manages live match data updates and event tracking"""
    
    def __init__(self, event_id: str, refresh_interval: int = 30):
        """
        Initialize live match manager
        
        Args:
            event_id: ESPN event ID for the match
            refresh_interval: Seconds between API calls
        """
        self.event_id = event_id
        self.refresh_interval = refresh_interval
        self.client = ESPNAPIClient()
        
        # Track seen events to detect new ones
        self.seen_goals: Set[str] = set()
        self.seen_cards: Set[str] = set()
        
        # Current match state
        self.current_score: Dict[str, int] = {}
        self.match_status: str = ""
        self.match_time: str = ""
    
    def fetch_update(self) -> Dict[str, any]:
        """
        Fetch latest match data and detect changes
        
        Returns:
            Dictionary with match state and new events
        """
        status = self.client.get_live_match_status(self.event_id)
        events = self.client.get_match_events(self.event_id)
        
        if not status:
            return {"error": "Failed to fetch match data"}
        
        # Update current state
        self.match_status = status["status"]
        self.match_time = status["time"]
        
        # Track scores
        for team in status["competitors"]:
            self.current_score[team["team_name"]] = team["score"]
        
        # Detect new events
        new_goals = self._detect_new_goals(events)
        new_cards = self._detect_new_cards(events)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": self.match_status,
            "time": self.match_time,
            "score": self.current_score.copy(),
            "new_goals": new_goals,
            "new_cards": new_cards,
            "all_events": events
        }
    
    def _detect_new_goals(self, events: List[Dict]) -> List[Dict]:
        """Detect goals that haven't been seen before"""
        new_goals = []
        
        for event in events:
            if event["is_scoring"]:
                event_id = f"{event['minute']}-{event['team']}-{','.join(event['participants'])}"
                if event_id not in self.seen_goals:
                    self.seen_goals.add(event_id)
                    new_goals.append(event)
        
        return new_goals
    
    def _detect_new_cards(self, events: List[Dict]) -> List[Dict]:
        """Detect cards that haven't been seen before"""
        new_cards = []
        
        for event in events:
            if event["is_card"]:
                event_id = f"{event['minute']}-{event['team']}-{','.join(event['participants'])}"
                if event_id not in self.seen_cards:
                    self.seen_cards.add(event_id)
                    new_cards.append(event)
        
        return new_cards
    
    def monitor_live(self, callback=None):
        """
        Continuously monitor match and call callback on updates
        
        Args:
            callback: Function to call with update data (optional)
        """
        print(f"🔴 Monitoring live match {self.event_id}...")
        
        try:
            while True:
                update = self.fetch_update()
                
                if callback:
                    callback(update)
                else:
                    self._print_update(update)
                
                time.sleep(self.refresh_interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopped live monitoring")
    
    def _print_update(self, update: Dict):
        """Default update printer"""
        print(f"\n[{update['timestamp']}] {update['status']} ({update['time']})")
        
        # Print scores
        for team, score in update['score'].items():
            print(f"  {team}: {score}")
        
        # Print new goals
        if update['new_goals']:
            print("  ⚽ NEW GOALS:")
            for goal in update['new_goals']:
                players = ', '.join(goal['participants'])
                print(f"    {goal['minute']} - {goal['team']} - {players}")
        
        # Print new cards
        if update['new_cards']:
            print("  🟨 NEW CARDS:")
            for card in update['new_cards']:
                players = ', '.join(card['participants'])
                print(f"    {card['minute']} - {card['team']} - {players}")
