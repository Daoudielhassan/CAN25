import requests
import pandas as pd
import re
import sys
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

EVENT_ID = 732133
BASE_URL = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/caf.nations/summary"
URL = f"{BASE_URL}?event={EVENT_ID}&region=us&lang=en"

OUTPUT_PREFIX = f"afcon_{EVENT_ID}"

# ============================================================
# UTILS
# ============================================================

def camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [camel_to_snake(c) for c in df.columns]
    return df

def enforce_numeric(df: pd.DataFrame, exclude: set) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if col not in exclude:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# ============================================================
# EXTRACTION
# ============================================================

response = requests.get(URL)
response.raise_for_status()
data = response.json()

# ============================================================
# FACT_MATCH (header)
# ============================================================

comp = data["header"]["competitions"][0]

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

# ============================================================
# FACT_TEAM_MATCH (header + boxscore)
# ============================================================

team_rows = []

for team in comp["competitors"]:
    base = {
        "match_id": EVENT_ID,
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

# ============================================================
# BOXSCORE STATS
# ============================================================

boxscore_rows = []

if "boxscore" in data and "teams" in data["boxscore"]:
    for t in data["boxscore"]["teams"]:
        row = {
            "match_id": EVENT_ID,
            "team_id": int(t["team"]["id"])
        }
        for stat in t.get("statistics", []):
            row[stat["name"]] = stat["displayValue"]
        boxscore_rows.append(row)

boxscore_df = pd.DataFrame(boxscore_rows)

if not boxscore_df.empty:
    boxscore_df = normalize_columns(boxscore_df)
    boxscore_df = enforce_numeric(
        boxscore_df,
        exclude={"match_id", "team_id"}
    )

    fact_team_match = fact_team_match.merge(
        boxscore_df,
        on=["match_id", "team_id"],
        how="left"
    )

# ============================================================
# FACT_GOALS (events)
# ============================================================

goal_rows = []

for event in comp.get("details", []):
    if event.get("scoringPlay"):
        participants = event.get("participants", [])
        scorer = participants[0]["athlete"]["displayName"] if len(participants) > 0 else None
        assister = participants[1]["athlete"]["displayName"] if len(participants) > 1 else None

        goal_rows.append({
            "match_id": EVENT_ID,
            "minute": int(event["clock"]["displayValue"].replace("'", "")),
            "team_id": int(event["team"]["id"]),
            "scorer": scorer,
            "assister": assister,
            "penalty": event["penaltyKick"],
            "own_goal": event["ownGoal"]
        })

fact_goals = pd.DataFrame(goal_rows)

# ============================================================
# DIM_TEAM
# ============================================================

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

# ============================================================
# ANALYTICAL FEATURES
# ============================================================

if not fact_team_match.empty:
    fact_team_match["goal_difference"] = (
        fact_team_match["score"] -
        fact_team_match.groupby("match_id")["score"].transform("max")
    )

    if {"shots_on_target", "total_shots", "possession_pct", "pass_pct"}.issubset(fact_team_match.columns):
        fact_team_match["goal_efficiency"] = (
            fact_team_match["score"] / fact_team_match["shots_on_target"]
        )
        fact_team_match["domination_index"] = (
            0.4 * fact_team_match["possession_pct"] +
            0.3 * fact_team_match["pass_pct"] +
            0.3 * fact_team_match["shots_on_target"]
        )

# ============================================================
# EXPORT
# ============================================================

fact_match.to_csv(f"{OUTPUT_PREFIX}_fact_match.csv", index=False)
fact_team_match.to_csv(f"{OUTPUT_PREFIX}_fact_team_match.csv", index=False)
fact_goals.to_csv(f"{OUTPUT_PREFIX}_fact_goals.csv", index=False)
dim_team.to_csv(f"{OUTPUT_PREFIX}_dim_team.csv", index=False)

print("ETL AFCON TERMINÉ AVEC SUCCÈS")
print("Fichiers générés :")
print(f"- {OUTPUT_PREFIX}_fact_match.csv")
print(f"- {OUTPUT_PREFIX}_fact_team_match.csv")
print(f"- {OUTPUT_PREFIX}_fact_goals.csv")
print(f"- {OUTPUT_PREFIX}_dim_team.csv")
