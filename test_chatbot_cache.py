"""
Test chatbot with cache to save API quota
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chatbot import AFCONChatbot


def main():
    print("🤖 Testing AFCON Chatbot with Cache\n")
    
    # Initialize chatbot
    print("Initializing chatbot...")
    chatbot = AFCONChatbot(use_conversational=False)
    print("✅ Chatbot ready\n")
    
    # Test queries (these should use cache after first run)
    test_queries = [
        "Give me stats about Algeria",
        "Who scored for Morocco vs Comoros?",
        "What was the final score of Algeria vs Sudan?",
        "give me stats about algeria",  # Similar query (should hit cache)
        "Algeria stats",  # Similar query (should hit cache)
    ]
    
    print("="*60)
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-"*60)
        
        try:
            response = chatbot.chat(query)
            
            # Show cache status
            if response.get('cached'):
                print(f"💾 CACHED ({response.get('cache_type', 'unknown')})")
            else:
                print(f"🌐 NEW API CALL (response will be cached)")
            
            # Show answer (truncated)
            answer = response.get('answer', 'No answer')
            print(f"\n📝 Answer: {answer[:200]}...")
            
            # Show sources
            num_sources = response.get('num_sources', 0)
            print(f"📊 Sources: {num_sources}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-"*60)
    
    # Show cache stats
    print("\n" + "="*60)
    print("📊 CACHE STATISTICS")
    print("="*60)
    stats = chatbot.get_cache_stats()
    print(f"Total Cached Responses: {stats['total_entries']}")
    print(f"Total Cache Hits: {stats['total_hits']}")
    print(f"Cache TTL: {stats['ttl_hours']:.1f} hours")
    print(f"Similarity Threshold: {stats['similarity_threshold']*100:.0f}%")
    print(f"Cache Location: {stats['cache_file']}")
    
    print("\n✨ Cache is saving your API quota!")
    print("💡 Similar questions will use cached responses")


if __name__ == "__main__":
    main()
