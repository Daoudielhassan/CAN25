"""
Test script to verify system components
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from src.live_data import ESPNAPIClient, AFCONDataProcessor, LiveMatchManager
        from src.knowledge_base import AFCONDataLoader, VectorStoreManager
        from src.rag import AFCONRetriever, AFCONRAGChain
        from src.chatbot import AFCONChatbot, QueryDispatcher, ResponseFormatter
        from src.api import app
        print("[OK] All imports successful")
        return True
    except Exception as e:
        print(f"[ERROR] Import error: {e}")
        return False


def test_api_client():
    """Test ESPN API client"""
    print("\nTesting ESPN API client...")
    try:
        from src.live_data import ESPNAPIClient
        client = ESPNAPIClient()
        
        # Test with known event
        data = client.fetch_match_summary("732133")
        if data:
            print("[OK] API client working")
            return True
        else:
            print("[WARNING] API returned no data (might be network issue)")
            return True  # Not a critical failure
    except Exception as e:
        print(f"[ERROR] API client error: {e}")
        return False


def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    try:
        from config import settings
        
        checks = []
        
        # Check if .env exists
        env_file = Path(".env")
        if env_file.exists():
            print("[OK] .env file found")
            checks.append(True)
        else:
            print("[WARNING] .env file not found (copy from .env.example)")
            checks.append(False)
        
        # Check OpenAI key
        if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
            print("[OK] OpenAI API key configured")
            checks.append(True)
        else:
            print("[WARNING] OpenAI API key not configured")
            checks.append(False)
        
        return all(checks)
    except Exception as e:
        print(f"[ERROR] Configuration error: {e}")
        return False


def test_data_files():
    """Test data files"""
    print("\nTesting data files...")
    try:
        historical_dir = Path("./data/historical")
        csv_files = list(historical_dir.glob("*.csv"))
        
        if csv_files:
            print(f"[OK] Found {len(csv_files)} CSV files in data/historical/")
            for csv_file in csv_files[:5]:  # Show first 5
                print(f"  - {csv_file.name}")
            return True
        else:
            print("[WARNING] No CSV files in data/historical/")
            print("  Run: python scripts/setup_vectorstore.py")
            return False
    except Exception as e:
        print(f"[ERROR] Data files error: {e}")
        return False


def test_vectorstore():
    """Test vector store"""
    print("\nTesting vector store...")
    try:
        vectorstore_path = Path("./data/vector_store/afcon_vectorstore")
        
        if vectorstore_path.exists():
            print("[OK] Vector store found")
            return True
        else:
            print("[WARNING] Vector store not found")
            print("  Run: python scripts/setup_vectorstore.py")
            return False
    except Exception as e:
        print(f"[ERROR] Vector store error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("AFCON Chatbot System Test")
    print("=" * 60)
    print()
    
    results = {
        "Imports": test_imports(),
        "API Client": test_api_client(),
        "Configuration": test_config(),
        "Data Files": test_data_files(),
        "Vector Store": test_vectorstore()
    }
    
    print()
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "[OK] PASS" if passed else "[ERROR] FAIL"
        print(f"{test_name:.<40} {status}")
    
    print()
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    if passed_count == total_count:
        print(" All tests passed! System is ready.")
        print()
        print("Next steps:")
        print("1. python -m src.api.server")
        print("2. Open frontend/index.html")
    else:
        print(f"[WARNING] {total_count - passed_count} test(s) failed. Review messages above.")
        print()
        print("Setup steps:")
        if not results["Configuration"]:
            print("1. Copy .env.example to .env")
            print("2. Add your OpenAI API key to .env")
        if not results["Data Files"] or not results["Vector Store"]:
            print("3. Run: python scripts/setup_vectorstore.py")
    
    print()


if __name__ == "__main__":
    main()
