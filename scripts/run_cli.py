"""
Simple CLI interface for AFCON Chatbot
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.chatbot import AFCONChatbot, ResponseFormatter


def main():
    """Run CLI chatbot"""
    print("=" * 60)
    print("[SOCCER] AFCON Chatbot CLI")
    print("=" * 60)
    print()
    
    # Initialize chatbot
    print("Initializing chatbot...")
    try:
        chatbot = AFCONChatbot(use_conversational=True)
        print("[OK] Chatbot ready!")
    except Exception as e:
        print(f"[ERROR] Error initializing chatbot: {e}")
        print()
        print("Make sure you have:")
        print("1. Set up the vector store (python scripts/setup_vectorstore.py)")
        print("2. Configured .env with your OpenAI API key")
        return
    
    print()
    print("Commands:")
    print("  - Type your question")
    print("  - 'clear' - Clear conversation history")
    print("  - 'live <event_id>' - Set live match to monitor")
    print("  - 'quit' or 'exit' - Exit chatbot")
    print("=" * 60)
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ["quit", "exit"]:
                print("\nGoodbye! [SOCCER]")
                break
            
            if user_input.lower() == "clear":
                result = chatbot.clear_conversation()
                print(f"\n[OK] {result['message']}\n")
                continue
            
            if user_input.lower().startswith("live "):
                event_id = user_input[5:].strip()
                chatbot.set_live_match(event_id)
                print(f"\n[OK] Now monitoring match: {event_id}\n")
                continue
            
            # Process query
            print("\n Thinking...\n")
            response = chatbot.chat(user_input)
            
            # Format and display response
            formatted = ResponseFormatter.format_for_console(response)
            print(formatted)
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! [SOCCER]")
            break
        except Exception as e:
            print(f"\n[ERROR] Error: {e}\n")


if __name__ == "__main__":
    main()
