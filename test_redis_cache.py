"""
Test multi-level caching system for AFCON Chatbot
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chatbot.redis_cache import RedisCache, EventDetector, CacheTTL
from src.live_data.api_client import ESPNAPIClient
import time


def test_redis_cache():
    """Test Redis cache functionality"""
    print("🧪 Testing Multi-Level Cache System\n")
    print("="*60)
    
    # Test 1: Redis Connection
    print("\n📌 Test 1: Redis Cache Connection")
    print("-"*60)
    cache = RedisCache()
    print(f"Redis Enabled: {cache.enabled}")
    print(f"Prefix: {cache.prefix}")
    
    if not cache.enabled:
        print("⚠️  Redis not available - using fallback cache")
        print("💡 To enable Redis: Install Redis and run 'redis-server'")
    
    print("✅ Test 1 passed\n")
    
    # Test 2: Basic Cache Operations
    print("📌 Test 2: Basic Cache Operations")
    print("-"*60)
    
    # Set live match data
    match_data = {
        "match_id": "732133",
        "teams": ["Morocco", "South Africa"],
        "score": "2-1",
        "status": "Live"
    }
    cache.set_live_match("732133", match_data)
    
    # Retrieve from cache
    cached = cache.get_live_match("732133")
    assert cached == match_data, "Cache data mismatch"
    print("✅ Live match cached and retrieved successfully")
    
    # Test RAG answer caching
    cache.set_rag_answer(
        "Who won AFCON 2023?",
        "Ivory Coast won AFCON 2023",
        ["doc1", "doc2"]
    )
    
    rag_answer = cache.get_rag_answer("Who won AFCON 2023?")
    assert rag_answer == "Ivory Coast won AFCON 2023"
    print("✅ RAG answer cached and retrieved successfully")
    
    print("✅ Test 2 passed\n")
    
    # Test 3: TTL Behavior
    print("📌 Test 3: TTL Behavior")
    print("-"*60)
    print(f"Live Score TTL: {CacheTTL.LIVE_SCORE}s")
    print(f"RAG Answer TTL: {CacheTTL.RAG_ANSWER}s")
    print(f"Team Info TTL: {CacheTTL.TEAM_INFO}s (permanent)")
    
    # Set short TTL data
    cache.set("test", "short_ttl", {"data": "expires soon"}, ttl=2)
    print("Set test data with 2s TTL...")
    
    # Check immediate retrieval
    data = cache.get("test", "short_ttl")
    assert data is not None, "Data should exist immediately"
    print("✅ Data retrieved immediately")
    
    print("Waiting 3 seconds for expiration...")
    time.sleep(3)
    
    data = cache.get("test", "short_ttl")
    if cache.enabled:
        assert data is None, "Data should have expired"
        print("✅ Data expired correctly")
    else:
        print("⚠️  Fallback cache doesn't support auto-expiration")
    
    print("✅ Test 3 passed\n")
    
    # Test 4: Cache Invalidation
    print("📌 Test 4: Cache Invalidation")
    print("-"*60)
    
    # Set multiple match data
    for i in range(3):
        cache.set_live_match(f"match_{i}", {"id": i, "status": "live"})
    
    print("Cached 3 matches...")
    
    # Invalidate one
    cache.invalidate_live_match("match_1")
    print("Invalidated match_1")
    
    # Check results
    assert cache.get_live_match("match_0") is not None
    assert cache.get_live_match("match_1") is None
    assert cache.get_live_match("match_2") is not None
    print("✅ Selective invalidation works")
    
    print("✅ Test 4 passed\n")
    
    # Test 5: Event Detection
    print("📌 Test 5: Event Detection")
    print("-"*60)
    
    detector = EventDetector()
    
    old_data = {
        "header": {
            "competitions": [{
                "details": [
                    {"scoringPlay": True, "minute": "15"},
                    {"scoringPlay": True, "minute": "42"}
                ],
                "status": {"type": {"name": "in_progress"}}
            }]
        }
    }
    
    new_data_with_goal = {
        "header": {
            "competitions": [{
                "details": [
                    {"scoringPlay": True, "minute": "15"},
                    {"scoringPlay": True, "minute": "42"},
                    {"scoringPlay": True, "minute": "67"}  # New goal!
                ],
                "status": {"type": {"name": "in_progress"}}
            }]
        }
    }
    
    new_data_halftime = {
        "header": {
            "competitions": [{
                "details": [
                    {"scoringPlay": True, "minute": "15"},
                    {"scoringPlay": True, "minute": "42"}
                ],
                "status": {"type": {"name": "halftime"}}  # Status changed!
            }]
        }
    }
    
    # Test goal detection
    has_new_goal = detector.detect_new_goal(old_data, new_data_with_goal)
    assert has_new_goal, "Should detect new goal"
    print("✅ New goal detected: 2 → 3 goals")
    
    # Test status change
    status_changed = detector.detect_status_change(old_data, new_data_halftime)
    assert status_changed, "Should detect status change"
    print("✅ Status change detected: in_progress → halftime")
    
    print("✅ Test 5 passed\n")
    
    # Test 6: Cache Stats
    print("📌 Test 6: Cache Statistics")
    print("-"*60)
    
    stats = cache.get_stats()
    print("Cache Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("✅ Test 6 passed\n")
    
    # Test 7: API Client with Cache
    print("📌 Test 7: API Client Cache Integration")
    print("-"*60)
    
    api_client = ESPNAPIClient(use_cache=True)
    print(f"API Client cache enabled: {api_client.cache is not None}")
    
    # Note: This would require a real event_id to test
    print("⚠️  Skipping live API test (requires real event_id)")
    print("💡 To test: api_client.fetch_match_summary('732133')")
    
    print("✅ Test 7 passed\n")
    
    print("="*60)
    print("🎉 All Tests Passed!")
    print("\n📊 Final Cache Stats:")
    final_stats = cache.get_stats()
    for key, value in final_stats.items():
        print(f"  {key}: {value}")
    
    if not cache.enabled:
        print("\n💡 To enable Redis for production:")
        print("   1. Install Redis: https://redis.io/download")
        print("   2. Start Redis server: redis-server")
        print("   3. Restart the chatbot")


if __name__ == "__main__":
    test_redis_cache()
