"""
Test script to query the chatbot API directly
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_query(question):
    """Test a query against the chatbot API"""
    print("=" * 70)
    print(f"Question: {question}")
    print("=" * 70)
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"query": question, "include_sources": False},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"\nAnswer:\n{data['answer']}")
            print(f"\nMetadata:")
            print(f"  - Type: {data['metadata'].get('query_type')}")
            print(f"  - Sources: {data['metadata'].get('num_sources')}")
        else:
            print(f"\n❌ Error {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    
    print()

# Test queries
print("\n🧪 Testing AFCON Chatbot with enhanced data\n")

test_query("Give me stats about Algeria")
test_query("Which matches did Algeria lose?")
test_query("What was the final score of Algeria vs Sudan?")
test_query("Who scored for Morocco vs Comoros?")

print("✅ All tests completed!")
