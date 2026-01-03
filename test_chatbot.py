"""
Test script for chatbot initialization
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.chatbot import AFCONChatbot


def main():
    """Test chatbot initialization"""
    print("=" * 60)
    print("Testing Chatbot Initialization")
    print("=" * 60)
    print()
    
    try:
        print("🔄 Initializing chatbot...")
        chatbot = AFCONChatbot()
        print("✅ Chatbot initialized successfully!")
        print()
        
        # Test a simple query
        print("Testing simple query...")
        response = chatbot.chat("Hello! Tell me about AFCON 2025.")
        
        print()
        print("=" * 60)
        print("Response:")
        print("=" * 60)
        print(response.get("answer", "No answer"))
        print()
        print(f"Type: {response.get('type', 'unknown')}")
        print(f"Success: {response.get('success', False)}")
        print()
        
        print("✅ Chatbot test successful!")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
