"""
Quick start script - runs all necessary setup steps
"""
import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")


def check_env_file():
    """Check if .env file exists"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("Creating .env from .env.example...")
        
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print("✓ Created .env file")
            print()
            print("⚠️  IMPORTANT: Edit .env and add your OpenAI API key!")
            print("   Open .env and replace 'your_openai_api_key_here'")
            print()
            return False
        else:
            print("✗ .env.example not found!")
            return False
    
    # Check if API key is configured
    with open(env_file) as f:
        content = f.read()
        if "your_openai_api_key_here" in content:
            print("⚠️  OpenAI API key not configured in .env")
            print("   Please edit .env and add your actual API key")
            return False
    
    print("✓ .env file configured")
    return True


def install_dependencies():
    """Install required packages"""
    print_header("Installing Dependencies")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("\n✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("\n✗ Failed to install dependencies")
        return False


def setup_vectorstore():
    """Setup vector store"""
    print_header("Setting Up Vector Store")
    
    try:
        subprocess.run(
            [sys.executable, "scripts/setup_vectorstore.py"],
            check=True
        )
        print("\n✓ Vector store setup complete")
        return True
    except subprocess.CalledProcessError:
        print("\n✗ Failed to setup vector store")
        return False


def run_tests():
    """Run system tests"""
    print_header("Running System Tests")
    
    try:
        subprocess.run(
            [sys.executable, "scripts/test_system.py"],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        print("\n⚠️  Some tests failed")
        return False


def main():
    """Run quick start process"""
    print_header("🚀 AFCON Chatbot Quick Start")
    
    print("This script will:")
    print("1. Check environment configuration")
    print("2. Install dependencies")
    print("3. Setup vector store")
    print("4. Run system tests")
    print()
    
    input("Press Enter to continue...")
    
    # Step 1: Check environment
    print_header("Step 1: Environment Configuration")
    if not check_env_file():
        print("\n⚠️  Please configure .env file and run this script again")
        print(f"   python {Path(__file__).name}")
        return
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print("\n✗ Setup failed at dependency installation")
        return
    
    # Step 3: Setup vector store
    if not setup_vectorstore():
        print("\n⚠️  Vector store setup failed")
        print("   You can retry later with: python scripts/setup_vectorstore.py")
    
    # Step 4: Run tests
    run_tests()
    
    # Final instructions
    print_header("🎉 Setup Complete!")
    print("Next steps:")
    print()
    print("1. Start the API server:")
    print("   python -m src.api.server")
    print()
    print("2. Use the chatbot:")
    print("   • Web UI: Open frontend/index.html in your browser")
    print("   • CLI: python scripts/run_cli.py")
    print("   • API Docs: http://localhost:8000/docs")
    print()
    print("Need help? Check SETUP.md for detailed instructions")
    print()


if __name__ == "__main__":
    main()
