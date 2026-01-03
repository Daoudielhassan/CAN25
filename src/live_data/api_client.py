"""
ESPN API Client for fetching AFCON live data
"""
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from config import settings
from ..chatbot.redis_cache import RedisCache, EventDetector


class ESPNAPIClient:
    """Client for interacting with ESPN AFCON API"""
    
    def __init__(self, use_cache: bool = True):
        self.base_url = settings.espn_base_url
        self.session = requests.Session()
        self.cache = RedisCache() if use_cache else None
        self.event_detector = EventDetector()
        self._last_match_data: Dict[str, Dict] = {}  # Track previous state for event detection
    
    def fetch_match_summary(self, event_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Fetch comprehensive match summary including stats and events
        Uses Redis cache with 20s TTL and event-based invalidation
        
        Args:
            event_id: ESPN event ID for the match
            force_refresh: Bypass cache and fetch fresh data
            
        Returns:
            JSON response with match data or None if request fails
        """
        # Check cache first (unless force refresh)
        if self.cache and not force_refresh:
            cached = self.cache.get_live_match(event_id)
            if cached:
                return cached
        
        # Fetch from API
        url = f"{self.base_url}/summary"
        params = {
            "event": event_id,
            "region": "us",
            "lang": "en"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Event detection and cache invalidation
            if self.cache:
                old_data = self._last_match_data.get(event_id)
                
                if old_data:
                    # Check for new goals
                    if self.event_detector.detect_new_goal(old_data, data):
                        print(f"⚽ NEW GOAL DETECTED! Invalidating cache for {event_id}")
                        self.cache.invalidate_live_match(event_id)
                    
                    # Check for status change (HT, FT)
                    elif self.event_detector.detect_status_change(old_data, data):
                        print(f"🔔 MATCH STATUS CHANGED! Invalidating cache for {event_id}")
                        self.cache.invalidate_live_match(event_id)
                
                # Cache the new data
                self.cache.set_live_match(event_id, data)
                self._last_match_data[event_id] = data
            
            return data
            
        except requests.RequestException as e:
            print(f"Error fetching match summary: {e}")
            return None
    
    def fetch_scoreboard(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Fetch scoreboard for a specific date
        
        Args:
            date: Date in YYYYMMDD format
            
        Returns:
            JSON response with scoreboard data or None if request fails
        """
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/caf.nations/scoreboard"
        params = {
            "dates": date,
            "region": "us",
            "lang": "en",
            "contentorigin": "espn"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching scoreboard: {e}")
            return None
    
    def get_live_match_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a live match (cached with 30s TTL)
        
        Args:
            event_id: ESPN event ID for the match
            
        Returns:
            Dictionary with match status information
        """
        # Check status cache
        if self.cache:
            cached = self.cache.get("status", event_id)
            if cached:
                return cached
        
        data = self.fetch_match_summary(event_id)
        if not data:
            return None
        
        header = data.get("header", {})
        comp = header.get("competitions", [{}])[0]
        
        status_info = {
            "match_id": header.get("id"),
            "status": comp.get("status", {}).get("type", {}).get("description"),
            "time": comp.get("status", {}).get("type", {}).get("detail"),
            "competitors": self._parse_competitors(comp)
        }
        
        # Cache status (30s TTL)
        if self.cache:
            self.cache.set("status", event_id, status_info, 30)
        
        return status_info
    
    def get_match_events(self, event_id: str) -> List[Dict[str, Any]]:
        """
        Extract all match events (goals, cards, substitutions)
        Cached with 30s TTL, invalidated on new events
        
        Args:
            event_id: ESPN event ID for the match
            
        Returns:
            List of event dictionaries
        """
        # Check events cache
        if self.cache:
            cached = self.cache.get_match_events(event_id)
            if cached:
                return cached
        
        data = self.fetch_match_summary(event_id)
        if not data:
            return []
        
        comp = data.get("header", {}).get("competitions", [{}])[0]
        details = comp.get("details", [])
        
        events = []
        for event in details:
            events.append({
                "minute": event.get("clock", {}).get("displayValue", ""),
                "type": event.get("type", {}).get("text", ""),
                "team": event.get("team", {}).get("displayName", ""),
                "is_scoring": event.get("scoringPlay", False),
                "is_card": "card" in event.get("type", {}).get("text", "").lower(),
                "participants": [
                    p["athlete"]["displayName"] 
                    for p in event.get("participants", [])
                ]
            })
        
        # Cache events (30s TTL)
        if self.cache:
            self.cache.set_match_events(event_id, events)
        
        return events
    
    def _parse_competitors(self, comp: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse competitor information from competition data"""
        competitors = []
        for team in comp.get("competitors", []):
            competitors.append({
                "team_id": team["team"]["id"],
                "team_name": team["team"]["displayName"],
                "score": team["score"],
                "home_away": team["homeAway"],
                "winner": team.get("winner", False)
            })
        return competitors
