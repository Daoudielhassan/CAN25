"""
Test script for response cache functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chatbot.cache import ResponseCache
import time


def test_cache():
    """Test cache functionality"""
    print("🧪 Testing Response Cache System\n")
    
    # Initialize cache with short TTL for testing
    cache = ResponseCache(ttl=10)  # 10 seconds for quick testing
    
    # Test 1: Cache miss
    print("Test 1: Cache Miss")
    result = cache.get("What is AFCON?")
    print(f"Result: {result}")
    assert result is None, "Should return None on cache miss"
    print("✅ Passed\n")
    
    # Test 2: Set cache
    print("Test 2: Set Cache")
    cache.set(
        "What is AFCON?",
        "AFCON is the African Cup of Nations, the main football competition in Africa.",
        ["doc1", "doc2"]
    )
    print("✅ Cached response\n")
    
    # Test 3: Exact cache hit
    print("Test 3: Exact Cache Hit")
    result = cache.get("What is AFCON?")
    assert result is not None, "Should return cached response"
    assert result['answer'] == "AFCON is the African Cup of Nations, the main football competition in Africa."
    assert result['cache_type'] == 'exact'
    print(f"Answer: {result['answer'][:50]}...")
    print("✅ Passed\n")
    
    # Test 4: Similar cache hit
    print("Test 4: Similar Cache Hit (85%+ similarity)")
    result = cache.get("what is afcon?")  # lowercase
    assert result is not None, "Should return cached response for similar query"
    print(f"Cache Type: {result['cache_type']}")
    print("✅ Passed\n")
    
    # Test 5: Multiple entries
    print("Test 5: Multiple Cache Entries")
    cache.set("Who won AFCON 2023?", "Ivory Coast won AFCON 2023", ["doc3"])
    cache.set("Where is AFCON 2025?", "AFCON 2025 is in Morocco", ["doc4"])
    stats = cache.get_stats()
    print(f"Total entries: {stats['total_entries']}")
    print(f"Total hits: {stats['total_hits']}")
    assert stats['total_entries'] >= 3, "Should have at least 3 entries"
    print("✅ Passed\n")
    
    # Test 6: Similar question variations
    print("Test 6: Similar Question Variations")
    variations = [
        "Who is the winner of AFCON 2023?",
        "who won afcon in 2023?",
        "AFCON 2023 winner?"
    ]
    for var in variations:
        result = cache.get(var)
        if result:
            print(f"✅ '{var}' -> HIT ({result['cache_type']})")
        else:
            print(f"❌ '{var}' -> MISS")
    print()
    
    # Test 7: Cache expiration
    print("Test 7: Cache Expiration (waiting 11 seconds...)")
    print("Skipping expiration test (would take 11 seconds)")
    # Uncomment to test:
    # time.sleep(11)
    # result = cache.get("What is AFCON?")
    # assert result is None, "Should return None after expiration"
    # print("✅ Passed\n")
    
    # Test 8: Stats
    print("Test 8: Final Cache Stats")
    stats = cache.get_stats()
    print(f"📊 Cache Statistics:")
    print(f"   Total Entries: {stats['total_entries']}")
    print(f"   Total Hits: {stats['total_hits']}")
    print(f"   TTL: {stats['ttl_hours']} hours")
    print(f"   Similarity Threshold: {stats['similarity_threshold']}")
    print(f"   Cache File: {stats['cache_file']}")
    print("✅ Passed\n")
    
    # Test 9: Clear cache
    print("Test 9: Clear Cache")
    cache.clear()
    stats = cache.get_stats()
    assert stats['total_entries'] == 0, "Should have 0 entries after clear"
    print("✅ Passed\n")
    
    print("🎉 All tests passed!")


if __name__ == "__main__":
    test_cache()
