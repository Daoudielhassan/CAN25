import requests
import time
from datetime import datetime

# =============================
# CONFIGURATION
# =============================
EVENT_ID = "732133"  # Comoros vs Morocco AFCON 2025
API_URL = f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/caf.nations/summary?event={EVENT_ID}"
REFRESH_INTERVAL = 30  # seconds

# In-memory storage for live events
last_goals = set()

# =============================
# FUNCTIONS
# =============================

def fetch_live_match():
    """
    Fetch live match data from ESPN API and return structured info.
    """
    resp = requests.get(API_URL)
    if resp.status_code != 200:
        print("Error fetching data:", resp.status_code)
        return None
    data = resp.json()
    match_data = data.get("header", {}).get("competitions", [])[0]
    return match_data

def parse_competitors(match_data):
    """
    Extract basic score info for both teams.
    """
    competitors = match_data.get("competitors", [])
    scores = {}
    for team in competitors:
        scores[team['team']['displayName']] = {
            "score": team['score'],
            "home_away": team['homeAway'],
            "winner": team['winner']
        }
    return scores

def parse_goals(match_data):
    """
    Extract scoring events (minute, team, players).
    """
    goals = []
    details = match_data.get("details", [])
    for event in details:
        if event.get("scoringPlay", False):
            clock = event.get("clock", {}).get("displayValue", "")
            team = event.get("team", {}).get("displayName", "")
            players = [p['athlete']['displayName'] for p in event.get("participants", [])]
            goal_id = f"{clock}-{team}-{','.join(players)}"
            if goal_id not in last_goals:
                last_goals.add(goal_id)
                goals.append({
                    "minute": clock,
                    "team": team,
                    "players": players
                })
    return goals

def print_live_update():
    """
    Fetch, parse, and print live match info.
    """
    match_data = fetch_live_match()
    if not match_data:
        return

    scores = parse_competitors(match_data)
    goals = parse_goals(match_data)

    # Match time & status
    status = match_data.get("status", {}).get("type", {}).get("description", "Unknown")
    match_time = match_data.get("status", {}).get("type", {}).get("detail", "")
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Match Status: {status} ({match_time})")
    
    # Scores
    for team, info in scores.items():
        print(f"{team} ({info['home_away']}): {info['score']}")

    # Goals
    if goals:
        print("New Goals:")
        for g in goals:
            print(f"  {g['minute']} - {g['team']} - Scorer(s): {', '.join(g['players'])}")
    else:
        print("No new goals.")

# =============================
# MAIN LOOP
# =============================
if __name__ == "__main__":
    print("Live AFCON Chatbot: Fetching live updates...")
    try:
        while True:
            print_live_update()
            time.sleep(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping live AFCON chatbot.")
