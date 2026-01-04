"""
Script to initialize vector store with historical AFCON data
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge_base import AFCONDataLoader, VectorStoreManager


def main():
    """Initialize vector store with historical data"""
    print("=" * 60)
    print("AFCON Vector Store Setup")
    print("=" * 60)
    print()
    
    # Step 1: Load historical data
    print(" Step 1: Loading historical data...")
    loader = AFCONDataLoader(data_dir="./data/historical")
    
    # Move existing CSV files to historical directory
    print("   Moving existing CSV files to data/historical/")
    import shutil
    csv_files = list(Path(".").glob("*.csv"))
    for csv_file in csv_files:
        if "afcon" in csv_file.name.lower() or "match" in csv_file.name.lower():
            try:
                dest = Path("./data/historical") / csv_file.name
                if not dest.exists():
                    shutil.copy(csv_file, dest)
                    print(f"   [OK] Copied {csv_file.name}")
            except Exception as e:
                print(f"   [ERROR] Error copying {csv_file.name}: {e}")
    
    print()
    documents = loader.load_all_documents()
    
    if not documents:
        print("[ERROR] No documents loaded. Please add CSV files to data/historical/")
        return
    
    print()
    
    # Step 2: Create vector store
    print("[LOADING] Step 2: Creating vector store...")
    vectorstore_manager = VectorStoreManager()
    vectorstore_manager.create_vectorstore(documents)
    
    print()
    
    # Step 3: Save vector store
    print("[SAVE] Step 3: Saving vector store...")
    vectorstore_manager.save_vectorstore("afcon_vectorstore")
    
    print()
    print("=" * 60)
    print("[OK] Vector store setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Configure your .env file with OpenAI API key")
    print("2. Run the API server: python -m src.api.server")
    print("3. Open frontend/index.html in your browser")
    print()


if __name__ == "__main__":
    main()
