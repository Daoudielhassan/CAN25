"""
Multi-level caching system for AFCON Chatbot
Implements Redis cache with smart TTL strategy
"""
import redis
import json
import hashlib
import time
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum


class CacheLevel(Enum):
    """Cache levels for different data types"""
    LIVE_SCORE = "live_score"
    LIVE_EVENTS = "live_events"
    MATCH_STATUS = "match_status"
    TEAM_INFO = "team_info"
    STANDINGS = "standings"
    RAG_ANSWER = "rag_answer"
    HISTORICAL = "historical"


class CacheTTL:
    """TTL configurations for different data types (in seconds)"""
    LIVE_SCORE = 20  # 20 seconds for live scores
    LIVE_EVENTS = 30  # 30 seconds for match events
    MATCH_STATUS = 30  # 30 seconds for match status
    TEAM_INFO = 86400 * 365  # 1 year (essentially forever)
    STANDINGS = 180  # 3 minutes
    RAG_ANSWER = 3600  # 1 hour for RAG responses
    HISTORICAL = 86400  # 24 hours for historical data


class RedisCache:
    """Redis-based cache with smart TTL and event-based invalidation"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        decode_responses: bool = True,
        prefix: str = "afcon"
    ):
        """
        Initialize Redis cache
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            decode_responses: Decode responses to strings
            prefix: Key prefix for namespacing
        """
        self.prefix = prefix
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=decode_responses,
                socket_timeout=2,
                socket_connect_timeout=2
            )
            # Test connection
            self.client.ping()
            self.enabled = True
            print(f"✅ Redis cache connected: {host}:{port}")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            print(f"⚠️  Redis not available: {e}")
            print("💡 Falling back to in-memory cache")
            self.enabled = False
            self.fallback_cache: Dict[str, Dict[str, Any]] = {}
    
    def _make_key(self, cache_type: str, identifier: str) -> str:
        """Create namespaced cache key"""
        return f"{self.prefix}:{cache_type}:{identifier}"
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query string"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get(self, cache_type: str, identifier: str) -> Optional[Any]:
        """
        Get cached data
        
        Args:
            cache_type: Type of cached data (e.g., 'live', 'team', 'rag')
            identifier: Unique identifier (event_id, team_id, query_hash)
            
        Returns:
            Cached data or None if not found
        """
        key = self._make_key(cache_type, identifier)
        
        if self.enabled:
            try:
                cached = self.client.get(key)
                if cached:
                    print(f"✅ Redis HIT: {cache_type}:{identifier[:20]}...")
                    return json.loads(cached)
            except Exception as e:
                print(f"⚠️  Redis get error: {e}")
                return None
        else:
            # Fallback to in-memory cache
            entry = self.fallback_cache.get(key)
            if entry and time.time() < entry['expires']:
                print(f"✅ Memory HIT: {cache_type}:{identifier[:20]}...")
                return entry['data']
        
        print(f"❌ Cache MISS: {cache_type}:{identifier[:20]}...")
        return None
    
    def set(
        self,
        cache_type: str,
        identifier: str,
        data: Any,
        ttl: Optional[int] = None
    ):
        """
        Set cached data with TTL
        
        Args:
            cache_type: Type of cached data
            identifier: Unique identifier
            data: Data to cache
            ttl: Time to live in seconds (None = no expiration)
        """
        key = self._make_key(cache_type, identifier)
        
        if self.enabled:
            try:
                serialized = json.dumps(data, ensure_ascii=False)
                if ttl:
                    self.client.setex(key, ttl, serialized)
                else:
                    self.client.set(key, serialized)
                print(f"💾 Redis SET: {cache_type}:{identifier[:20]}... (TTL: {ttl}s)")
            except Exception as e:
                print(f"⚠️  Redis set error: {e}")
        else:
            # Fallback to in-memory cache
            expires = time.time() + ttl if ttl else float('inf')
            self.fallback_cache[key] = {
                'data': data,
                'expires': expires
            }
            print(f"💾 Memory SET: {cache_type}:{identifier[:20]}... (TTL: {ttl}s)")
    
    def delete(self, cache_type: str, identifier: str):
        """Delete cached data"""
        key = self._make_key(cache_type, identifier)
        
        if self.enabled:
            try:
                self.client.delete(key)
                print(f"🗑️  Redis DELETE: {cache_type}:{identifier[:20]}...")
            except Exception as e:
                print(f"⚠️  Redis delete error: {e}")
        else:
            if key in self.fallback_cache:
                del self.fallback_cache[key]
                print(f"🗑️  Memory DELETE: {cache_type}:{identifier[:20]}...")
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., 'afcon:live:*')
        """
        if self.enabled:
            try:
                keys = self.client.keys(pattern)
                if keys:
                    self.client.delete(*keys)
                    print(f"🗑️  Redis INVALIDATE: {len(keys)} keys matching {pattern}")
            except Exception as e:
                print(f"⚠️  Redis invalidate error: {e}")
        else:
            # Fallback pattern matching
            to_delete = [k for k in self.fallback_cache.keys() if pattern.replace('*', '') in k]
            for key in to_delete:
                del self.fallback_cache[key]
            print(f"🗑️  Memory INVALIDATE: {len(to_delete)} keys")
    
    def get_live_match(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get cached live match data"""
        return self.get("live", event_id)
    
    def set_live_match(self, event_id: str, data: Dict[str, Any]):
        """Cache live match data with 20s TTL"""
        self.set("live", event_id, data, CacheTTL.LIVE_SCORE)
    
    def get_match_events(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get cached match events"""
        return self.get("events", event_id)
    
    def set_match_events(self, event_id: str, data: Dict[str, Any]):
        """Cache match events with 30s TTL"""
        self.set("events", event_id, data, CacheTTL.LIVE_EVENTS)
    
    def get_team_info(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get cached team info (permanent)"""
        return self.get("team", team_id)
    
    def set_team_info(self, team_id: str, data: Dict[str, Any]):
        """Cache team info permanently"""
        self.set("team", team_id, data, CacheTTL.TEAM_INFO)
    
    def get_standings(self, group: str) -> Optional[Dict[str, Any]]:
        """Get cached standings"""
        return self.get("standings", group)
    
    def set_standings(self, group: str, data: Dict[str, Any]):
        """Cache standings with 3 minute TTL"""
        self.set("standings", group, data, CacheTTL.STANDINGS)
    
    def get_rag_answer(self, query: str) -> Optional[str]:
        """Get cached RAG answer"""
        query_hash = self._hash_query(query)
        result = self.get("rag", query_hash)
        return result['answer'] if result else None
    
    def set_rag_answer(self, query: str, answer: str, sources: list):
        """Cache RAG answer with 1 hour TTL"""
        query_hash = self._hash_query(query)
        data = {
            'query': query,
            'answer': answer,
            'sources': sources,
            'timestamp': time.time()
        }
        self.set("rag", query_hash, data, CacheTTL.RAG_ANSWER)
    
    def invalidate_live_match(self, event_id: str):
        """Invalidate all live data for a match (on goal/event)"""
        self.delete("live", event_id)
        self.delete("events", event_id)
        print(f"🔥 Invalidated live cache for match {event_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.enabled:
            try:
                info = self.client.info('stats')
                keyspace = self.client.info('keyspace')
                return {
                    'enabled': True,
                    'total_keys': keyspace.get('db0', {}).get('keys', 0),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                    'hit_rate': (
                        info.get('keyspace_hits', 0) / 
                        (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1))
                    ) * 100
                }
            except Exception as e:
                print(f"⚠️  Redis stats error: {e}")
                return {'enabled': True, 'error': str(e)}
        else:
            return {
                'enabled': False,
                'fallback': True,
                'total_keys': len(self.fallback_cache)
            }


class EventDetector:
    """Detect events to trigger cache invalidation"""
    
    @staticmethod
    def detect_new_goal(old_data: Dict, new_data: Dict) -> bool:
        """
        Detect if a new goal happened
        
        Args:
            old_data: Previous match data
            new_data: Current match data
            
        Returns:
            True if new goal detected
        """
        try:
            old_events = old_data.get("header", {}).get("competitions", [{}])[0].get("details", [])
            new_events = new_data.get("header", {}).get("competitions", [{}])[0].get("details", [])
            
            old_goals = len([e for e in old_events if e.get("scoringPlay")])
            new_goals = len([e for e in new_events if e.get("scoringPlay")])
            
            return new_goals > old_goals
        except Exception:
            return False
    
    @staticmethod
    def detect_status_change(old_data: Dict, new_data: Dict) -> bool:
        """
        Detect if match status changed (HT, FT, etc.)
        
        Args:
            old_data: Previous match data
            new_data: Current match data
            
        Returns:
            True if status changed
        """
        try:
            old_status = old_data.get("header", {}).get("competitions", [{}])[0].get("status", {}).get("type", {}).get("name")
            new_status = new_data.get("header", {}).get("competitions", [{}])[0].get("status", {}).get("type", {}).get("name")
            
            return old_status != new_status
        except Exception:
            return False
