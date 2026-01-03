import requests
import pandas as pd
from datetime import datetime, timedelta

# Constants
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/caf.nations/scoreboard"
SUMMARY_URL    = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/caf.nations/summary"

# ============================================================
# UTILS
# ============================================================

def get_afcon_dates():
    """AFCON 2025 full date range as YYYYMMDD strings."""
    start = datetime(2025, 12, 21)
    end   = datetime(2026, 1, 18)
    dates=[]
    while start <= end:
        dates.append(start.strftime("%Y%m%d"))
        start += timedelta(days=1)
    return dates

def fetch_matches_for_country(country):
    """Fetch events for AFCON dates and filter for the chosen country."""
    matches=[]
    for d in get_afcon_dates():
        resp = requests.get(SCOREBOARD_URL, params={"dates":d,"region":"us","lang":"en","contentorigin":"espn"})
        if resp.status_code != 200:
            continue
        data = resp.json()
        for ev in data.get("events", []):
            comps = ev.get("competitions", [])
            if not comps:
                continue
            comp= comps[0]
            teams = [c["team"]["displayName"] for c in comp.get("competitors", [])]
            if any(country.lower() in t.lower() for t in teams):
                # Format date nicely
                dt = ev.get("date")
                if dt:
                    dt = dt.replace("T"," ").replace("Z","")
                matches.append({
                    "eventId": ev.get("id"),
                    "date": dt,
                    "teams": " vs ".join(teams),
                    "status": ev.get("status", {}).get("type", {}).get("description",""),
                })
    return matches

def print_matches(matches):
    """Prints a numbered list of matches."""
    for i, m in enumerate(matches,1):
        print(f"{i}. {m['date']} | {m['teams']} | {m['status']}")

def choose_match(matches):
    """Prompts user to select from the list."""
    while True:
        try:
            idx = int(input("\nEnter match number: ")) - 1
            if 0 <= idx < len(matches):
                return matches[idx]
            print("Invalid number. Try again.")
        except ValueError:
            print("Enter a valid number.")

def fetch_summary(eventId):
    """Fetch summary stats for the selected match."""
    params = {"event": eventId, "region":"us","lang":"en","contentorigin":"espn"}
    r = requests.get(SUMMARY_URL, params=params)
    return r.json() if r.status_code == 200 else None

def save_summary(data, eventId):
    """Save team stats from summary to CSV and Excel."""
    team_stats=[]
    teams = data.get("boxscore", {}).get("teams", [])
    if not teams:
        print("No team stats found in summary.")
        return

    for t_block in teams:
        team = t_block.get("team", {}).get("displayName", "Unknown")
        stats = t_block.get("statistics", [])
        for stat in stats:
            team_stats.append({
                "Team": team,
                "Stat": stat.get("label"),
                "Value": stat.get("displayValue")
            })

    if not team_stats:
        print("No stats found for teams.")
        return

    # Save CSV
    df = pd.DataFrame(team_stats)
    csv_file = f"match_{eventId}_summary.csv"
    df.to_csv(csv_file, index=False)
    print(f"Saved CSV: {csv_file}")

    # Save Excel
    excel_file = f"match_{eventId}_summary.xlsx"
    df.to_excel(excel_file, index=False)
    print(f"Saved Excel: {excel_file}")

# ============================================================
# MAIN
# ============================================================

def main():
    country = input("Enter country name (e.g., Morocco): ").strip()
    print(f"\nFetching AFCON 2025 matches for {country}...\n")
    matches = fetch_matches_for_country(country)

    if not matches:
        print("No matches found for that country.")
        return

    print_matches(matches)
    selected = choose_match(matches)
    
    print("\nFetching detailed summary stats...\n")
    summary = fetch_summary(selected["eventId"])
    if not summary:
        print("No summary data available for this match.")
        return
    
    save_summary(summary, selected["eventId"])
    print("\nDone!")

if __name__ == "__main__":
    main()
