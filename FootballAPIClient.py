import requests
import csv
import time

LEAGUE = "caf.nations"
YEAR = "2025"

# 1) Fetch list of matches (eventId, competitionId)
def get_afcon_events(dates):
    base_score = "https://site.api.espn.com/apis/site/v2/sports/soccer/caf.nations/scoreboard"
    events_info = []
    for d in dates:
        r = requests.get(base_score, params={"dates": d, "lang":"en","region":"us"})
        if r.status_code != 200:
            continue
        data = r.json()
        for ev in data.get("events", []):
            comp = ev["competitions"][0]
            events_info.append({
                "eventId": ev["id"],
                "compId": comp["id"],
                "date": ev["date"],
                "teams": [x["team"]["displayName"] for x in comp["competitors"]]
            })
        time.sleep(0.5)
    return events_info

# 2) Query ESPN Core API for athlete list
def core_athletes():
    url = f"https://sports.core.api.espn.com/v2/sports/soccer/leagues/{LEAGUE}/athletes"
    r = requests.get(url, params={"limit":1000,"lang":"en","region":"us"})
    if r.status_code != 200:
        return []
    return r.json().get("items", [])

# 3) Query match detailed stats and odds
def core_match_info(event):
    eid = event["eventId"]
    cid = event["compId"]
    out = {"eventId":eid, "date":event["date"], "teams": event["teams"]}

    # odds
    odds_url = f"https://sports.core.api.espn.com/v2/sports/soccer/leagues/{LEAGUE}/events/{eid}/competitions/{cid}/odds"
    p_url   = f"https://sports.core.api.espn.com/v2/sports/soccer/leagues/{LEAGUE}/events/{eid}/competitions/{cid}/probabilities"
    stats_url = f"https://sports.core.api.espn.com/v2/sports/soccer/leagues/{LEAGUE}/events/{eid}/competitions/{cid}/statistics"

    for name,url in [("odds",odds_url),("prob",p_url),("stats",stats_url)]:
        r = requests.get(url, params={"lang":"en","region":"us"})
        if r.status_code == 200:
            out[name] = r.json()
        time.sleep(0.5)
    return out

# 4) Write output to CSV
def save_csv(data):
    with open("afcon2025_detailed.csv","w",newline="",encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["EventId","Date","Teams","Odds/Book","Win/Draw/Loss","MatchStats"])
        for row in data:
            writer.writerow([
                row.get("eventId"),
                row.get("date"),
                ";".join(row.get("teams", [])),
                row.get("odds"),
                row.get("prob"),
                row.get("stats")
            ])

# ----- Runner -----
# list all tournament dates from Dec 21 2025 to Jan 18 2026
def get_dates(start="2025-12-21", end="2026-01-18"):
    from datetime import datetime,timedelta
    s = datetime.strptime(start,"%Y-%m-%d")
    e = datetime.strptime(end,"%Y-%m-%d")
    dates=[]
    while s<=e:
        dates.append(s.strftime("%Y%m%d"))
        s += timedelta(days=1)
    return dates

events = get_afcon_events(get_dates())
print("Found events:", len(events))

# Load athletes
athletes = core_athletes()
print("Athletes:", len(athletes))

details=[]
for ev in events:
    info = core_match_info(ev)
    details.append(info)

save_csv(details)
print("Saved detailed CSV")
