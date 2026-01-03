"""
Comprehensive script to fetch ALL AFCON 2025 match data
Fetches all matches from Dec 21, 2025 to Jan 18, 2026 and processes them
"""
import requests
import pandas as pd
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/caf.nations/scoreboard"
SUMMARY_URL = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/caf.nations/summary"
OUTPUT_DIR = Path("data/historical")
DELAY_BETWEEN_REQUESTS = 1  # seconds

# ============================================================
# UTILITIES
# ============================================================

def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case"""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame column names"""
    df = df.copy()
    df.columns = [camel_to_snake(c) for c in df.columns]
    return df

def enforce_numeric(df: pd.DataFrame, exclude: set) -> pd.DataFrame:
    """Convert columns to numeric"""
    df = df.copy()
    for col in df.columns:
        if col not in exclude:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def get_afcon_dates():
    """Generate all dates for AFCON 2025 tournament"""
    start = datetime(2025, 12, 21)
    end = datetime(2026, 1, 18)
    dates = []
    while start <= end:
        dates.append(start.strftime("%Y%m%d"))
        start += timedelta(days=1)
    return dates

# ============================================================
# DATA FETCHING
# ============================================================

def fetch_all_match_events():
    """Fetch all match event IDs from the tournament"""
    print("=" * 60)
    print("Fetching all AFCON 2025 match events...")
    print("=" * 60)
    
    all_events = []
    dates = get_afcon_dates()
    
    for date in dates:
        print(f"\nChecking date: {date}")
        try:
            resp = requests.get(
                SCOREBOARD_URL,
                params={"dates": date, "region": "us", "lang": "en", "contentorigin": "espn"}
            )
            
            if resp.status_code != 200:
                print(f"  ⚠️  Failed to fetch: HTTP {resp.status_code}")
                continue
            
            data = resp.json()
            events = data.get("events", [])
            
            if events:
                print(f"  ✓ Found {len(events)} match(es)")
                for event in events:
                    comp = event.get("competitions", [{}])[0]
                    competitors = comp.get("competitors", [])
                    team_names = [c["team"]["displayName"] for c in competitors]
                    
                    event_info = {
                        "event_id": event["id"],
                        "date": event["date"],
                        "teams": " vs ".join(team_names),
                        "status": event.get("status", {}).get("type", {}).get("description", "Unknown"),
                        "competition_id": comp["id"]
                    }
                    all_events.append(event_info)
                    print(f"    • {event_info['teams']} ({event_info['status']})")
            else:
                print(f"  - No matches")
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    print(f"\n{'=' * 60}")
    print(f"Total matches found: {len(all_events)}")
    print(f"{'=' * 60}\n")
    
    return all_events

def fetch_match_summary(event_id: str):
    """Fetch detailed match summary"""
    try:
        resp = requests.get(
            SUMMARY_URL,
            params={"event": event_id, "region": "us", "lang": "en"}
        )
        
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"    ✗ Failed to fetch summary: HTTP {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"    ✗ Error fetching summary: {e}")
        return None

# ============================================================
# DATA PROCESSING
# ============================================================

def process_match_data(data, event_id: str):
    """Process match data into structured DataFrames"""
    try:
        comp = data["header"]["competitions"][0]
        
        # FACT_MATCH
        fact_match = pd.DataFrame([{
            "match_id": int(data["header"]["id"]),
            "date_utc": comp["date"],
            "season": data["header"]["season"]["year"],
            "competition": data["header"]["season"]["name"],
            "group_name": comp.get("groups", {}).get("name"),
            "status": comp["status"]["type"]["description"],
            "neutral_site": comp["neutralSite"],
            "venue_available": comp["boxscoreAvailable"]
        }])
        fact_match["date_utc"] = pd.to_datetime(fact_match["date_utc"])
        
        # FACT_TEAM_MATCH
        team_rows = []
        for team in comp["competitors"]:
            base = {
                "match_id": int(event_id),
                "team_id": int(team["team"]["id"]),
                "team_name": team["team"]["displayName"],
                "home_away": team["homeAway"],
                "score": int(team["score"]),
                "winner": team["winner"],
                "advance": team.get("advance", False),
                "group_name": team["groups"]["abbreviation"],
                "points": int(
                    next(
                        (r["summary"] for r in team["record"] if r["type"] == "points"),
                        0
                    )
                )
            }
            team_rows.append(base)
        
        fact_team_match = pd.DataFrame(team_rows)
        
        # BOXSCORE STATS
        if "boxscore" in data and "teams" in data["boxscore"]:
            boxscore_rows = []
            for t in data["boxscore"]["teams"]:
                row = {
                    "match_id": int(event_id),
                    "team_id": int(t["team"]["id"])
                }
                for stat in t.get("statistics", []):
                    row[stat["name"]] = stat["displayValue"]
                boxscore_rows.append(row)
            
            boxscore_df = pd.DataFrame(boxscore_rows)
            if not boxscore_df.empty:
                boxscore_df = normalize_columns(boxscore_df)
                boxscore_df = enforce_numeric(boxscore_df, exclude={"match_id", "team_id"})
                fact_team_match = fact_team_match.merge(
                    boxscore_df,
                    on=["match_id", "team_id"],
                    how="left"
                )
        
        # FACT_GOALS
        goal_rows = []
        for event in comp.get("details", []):
            if event.get("scoringPlay"):
                participants = event.get("participants", [])
                scorer = participants[0]["athlete"]["displayName"] if len(participants) > 0 else None
                assister = participants[1]["athlete"]["displayName"] if len(participants) > 1 else None
                
                minute_str = event["clock"]["displayValue"].replace("'", "").replace("+", "")
                try:
                    minute = int(minute_str.split()[0])
                except:
                    minute = 0
                
                goal_rows.append({
                    "match_id": int(event_id),
                    "minute": minute,
                    "team_id": int(event["team"]["id"]),
                    "scorer": scorer,
                    "assister": assister,
                    "penalty": event.get("penaltyKick", False),
                    "own_goal": event.get("ownGoal", False)
                })
        
        fact_goals = pd.DataFrame(goal_rows)
        
        # DIM_TEAM
        teams = []
        for t in comp["competitors"]:
            teams.append({
                "team_id": int(t["team"]["id"]),
                "team_name": t["team"]["displayName"],
                "abbreviation": t["team"]["abbreviation"],
                "country": t["team"]["location"],
                "color": t["team"]["color"]
            })
        dim_team = pd.DataFrame(teams).drop_duplicates()
        
        return {
            "fact_match": fact_match,
            "fact_team_match": fact_team_match,
            "fact_goals": fact_goals,
            "dim_team": dim_team
        }
        
    except Exception as e:
        print(f"    ✗ Error processing match data: {e}")
        return None

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    """Main execution function"""
    print("\n🏆 AFCON 2025 - Complete Data Extraction")
    print("=" * 60)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Fetch all match events
    all_events = fetch_all_match_events()
    
    if not all_events:
        print("\n❌ No matches found!")
        return
    
    # Save event list
    events_df = pd.DataFrame(all_events)
    events_df.to_csv(OUTPUT_DIR / "afcon_2025_all_events.csv", index=False)
    print(f"✓ Saved event list to: {OUTPUT_DIR / 'afcon_2025_all_events.csv'}")
    
    # Step 2: Process each match
    print(f"\n{'=' * 60}")
    print("Processing individual matches...")
    print(f"{'=' * 60}\n")
    
    all_fact_match = []
    all_fact_team_match = []
    all_fact_goals = []
    all_dim_team = []
    
    successful = 0
    failed = 0
    
    for i, event in enumerate(all_events, 1):
        event_id = event["event_id"]
        teams = event["teams"]
        
        print(f"[{i}/{len(all_events)}] Processing: {teams} (ID: {event_id})")
        
        # Fetch match summary
        print(f"    Fetching data...")
        data = fetch_match_summary(event_id)
        
        if not data:
            print(f"    ✗ Skipped\n")
            failed += 1
            continue
        
        # Process match data
        print(f"    Processing data...")
        processed = process_match_data(data, event_id)
        
        if processed:
            all_fact_match.append(processed["fact_match"])
            all_fact_team_match.append(processed["fact_team_match"])
            if not processed["fact_goals"].empty:
                all_fact_goals.append(processed["fact_goals"])
            all_dim_team.append(processed["dim_team"])
            
            print(f"    ✓ Success\n")
            successful += 1
        else:
            print(f"    ✗ Failed to process\n")
            failed += 1
        
        time.sleep(DELAY_BETWEEN_REQUESTS)  # Rate limiting
    
    # Step 3: Consolidate and save
    print(f"{'=' * 60}")
    print("Consolidating data...")
    print(f"{'=' * 60}\n")
    
    if all_fact_match:
        # Combine all dataframes
        final_fact_match = pd.concat(all_fact_match, ignore_index=True)
        final_fact_team_match = pd.concat(all_fact_team_match, ignore_index=True)
        final_dim_team = pd.concat(all_dim_team, ignore_index=True).drop_duplicates(subset=["team_id"])
        
        if all_fact_goals:
            final_fact_goals = pd.concat(all_fact_goals, ignore_index=True)
        else:
            final_fact_goals = pd.DataFrame()
        
        # Save consolidated files
        final_fact_match.to_csv(OUTPUT_DIR / "afcon_2025_fact_match.csv", index=False)
        final_fact_team_match.to_csv(OUTPUT_DIR / "afcon_2025_fact_team_match.csv", index=False)
        final_dim_team.to_csv(OUTPUT_DIR / "afcon_2025_dim_team.csv", index=False)
        
        if not final_fact_goals.empty:
            final_fact_goals.to_csv(OUTPUT_DIR / "afcon_2025_fact_goals.csv", index=False)
        
        print(f"✓ Saved consolidated files to: {OUTPUT_DIR}")
        print(f"\nFiles created:")
        print(f"  • afcon_2025_all_events.csv ({len(all_events)} matches)")
        print(f"  • afcon_2025_fact_match.csv ({len(final_fact_match)} matches)")
        print(f"  • afcon_2025_fact_team_match.csv ({len(final_fact_team_match)} team records)")
        print(f"  • afcon_2025_dim_team.csv ({len(final_dim_team)} teams)")
        if not final_fact_goals.empty:
            print(f"  • afcon_2025_fact_goals.csv ({len(final_fact_goals)} goals)")
    
    # Summary
    print(f"\n{'=' * 60}")
    print("EXECUTION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total matches found:     {len(all_events)}")
    print(f"Successfully processed:  {successful}")
    print(f"Failed:                  {failed}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

if __name__ == "__main__":
    main()
