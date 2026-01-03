"""
Script to monitor a live match and display updates
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.live_data import LiveMatchManager


def main():
    """Monitor live match"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/monitor_live_match.py <event_id>")
        print()
        print("Example: python scripts/monitor_live_match.py 732133")
        return
    
    event_id = sys.argv[1]
    
    print("=" * 60)
    print(f"🔴 Live Match Monitor - Event {event_id}")
    print("=" * 60)
    print()
    print("Press Ctrl+C to stop monitoring")
    print()
    
    manager = LiveMatchManager(event_id=event_id, refresh_interval=30)
    manager.monitor_live()


if __name__ == "__main__":
    main()
