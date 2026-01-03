"""
Example script showing how to use the chatbot with live mode
"""
from src.chatbot import AFCONChatbot

# Method 1: Initialize with live match directly
print("=" * 60)
print("Method 1: Initialize with live match")
print("=" * 60)
chatbot = AFCONChatbot(live_event_id="732160")
response = chatbot.chat("What's the current score?")
print(f"Answer: {response['answer']}")
print()

# Method 2: Start without live mode, then activate it
print("=" * 60)
print("Method 2: Activate live mode after initialization")
print("=" * 60)
chatbot2 = AFCONChatbot()  # No live mode initially

# Ask historical question first
response = chatbot2.chat("Who has won the most AFCON titles?")
print(f"Historical: {response['answer'][:100]}...")
print()

# Now activate live mode
chatbot2.set_live_match("732160")
response = chatbot2.chat("What's happening in this match?")
print(f"Live: {response['answer'][:100]}...")
print()

# Method 3: Switch between different live matches
print("=" * 60)
print("Method 3: Switch between live matches")
print("=" * 60)
chatbot3 = AFCONChatbot(live_event_id="732160")
print("Monitoring match 732160")

# Switch to different match
chatbot3.set_live_match("732161")
print("Now monitoring match 732161")
