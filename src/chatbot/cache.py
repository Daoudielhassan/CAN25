"""
Intelligent caching system for chatbot responses
Saves API quota by caching similar questions and responses
"""
import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any
from difflib import SequenceMatcher


class ResponseCache:
    """Cache for chatbot responses with similarity matching"""
    
    def __init__(self, cache_dir: str = "./data/cache", ttl: int = 86400):
        """
        Initialize response cache
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Time to live in seconds (default: 24 hours)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "response_cache.json"
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = self._load_cache()
        self.similarity_threshold = 0.85  # 85% similarity to consider a cache hit
        
    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired"""
        return (time.time() - timestamp) > self.ttl
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response for query
        
        Args:
            query: User query
            
        Returns:
            Cached response dict or None if not found/expired
        """
        # Clean expired entries
        self._clean_expired()
        
        # Try exact match first
        cache_key = self._get_cache_key(query)
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not self._is_expired(entry['timestamp']):
                print(f"[OK] Cache HIT (exact): {query[:50]}...")
                entry['hits'] = entry.get('hits', 0) + 1
                self._save_cache()
                return {
                    'answer': entry['answer'],
                    'sources': entry['sources'],
                    'cached': True,
                    'cache_type': 'exact'
                }
        
        # Try similarity match
        normalized_query = query.lower().strip()
        for key, entry in self.cache.items():
            if self._is_expired(entry['timestamp']):
                continue
                
            original_query = entry['query']
            similarity = self._calculate_similarity(normalized_query, original_query)
            
            if similarity >= self.similarity_threshold:
                print(f"[OK] Cache HIT (similar {similarity:.1%}): {query[:50]}...")
                entry['hits'] = entry.get('hits', 0) + 1
                self._save_cache()
                return {
                    'answer': entry['answer'],
                    'sources': entry['sources'],
                    'cached': True,
                    'cache_type': f'similar ({similarity:.1%})'
                }
        
        print(f"[ERROR] Cache MISS: {query[:50]}...")
        return None
    
    def set(self, query: str, answer: str, sources: list):
        """
        Cache a response
        
        Args:
            query: User query
            answer: Bot response
            sources: Source documents used
        """
        cache_key = self._get_cache_key(query)
        self.cache[cache_key] = {
            'query': query.lower().strip(),
            'answer': answer,
            'sources': sources,
            'timestamp': time.time(),
            'hits': 0
        }
        self._save_cache()
        print(f"[SAVE] Cached response for: {query[:50]}...")
    
    def _clean_expired(self):
        """Remove expired cache entries"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry['timestamp'])
        ]
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self._save_cache()
            print(f" Cleaned {len(expired_keys)} expired cache entries")
    
    def clear(self):
        """Clear entire cache"""
        self.cache = {}
        self._save_cache()
        print(" Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        total_hits = sum(entry.get('hits', 0) for entry in self.cache.values())
        
        return {
            'total_entries': total_entries,
            'total_hits': total_hits,
            'cache_file': str(self.cache_file),
            'ttl_hours': self.ttl / 3600,
            'similarity_threshold': self.similarity_threshold
        }
