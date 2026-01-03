"""
Test script for Gemini API
"""
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings


def test_gemini_chat():
    """Test Gemini chat model"""
    print("=" * 60)
    print("Testing Gemini Chat API")
    print("=" * 60)
    print()
    
    try:
        # Initialize Gemini chat model
        llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.7
        )
        
        print("✓ Gemini model initialized")
        print(f"✓ Model: {settings.gemini_model}")
        print()
        
        # Test simple query
        print("Testing simple query...")
        response = llm.invoke("Hello! Can you tell me about the AFCON 2025 tournament?")
        
        print("=" * 60)
        print("Response:")
        print("=" * 60)
        print(response.content)
        print()
        
        print("✅ Gemini API test successful!")
        
    except Exception as e:
        print("❌ Error testing Gemini API:")
        print(f"   {type(e).__name__}: {e}")
        return False
    
    return True


def test_gemini_streaming():
    """Test Gemini streaming responses"""
    print()
    print("=" * 60)
    print("Testing Gemini Streaming")
    print("=" * 60)
    print()
    
    try:
        llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.7
        )
        
        print("Streaming response:")
        print("-" * 60)
        
        for chunk in llm.stream("Tell me about Morocco's performance in AFCON tournaments."):
            print(chunk.content, end="", flush=True)
        
        print()
        print("-" * 60)
        print()
        print("✅ Streaming test successful!")
        
    except Exception as e:
        print("❌ Error testing streaming:")
        print(f"   {type(e).__name__}: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print()
    print("🚀 Starting Gemini API Tests")
    print()
    
    # Test 1: Basic chat
    success1 = test_gemini_chat()
    
    # Test 2: Streaming
    if success1:
        success2 = test_gemini_streaming()
    else:
        success2 = False
    
    print()
    print("=" * 60)
    if success1 and success2:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Please check your API key and quota.")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
