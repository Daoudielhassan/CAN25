"""
ETL module for processing and cleaning AFCON data
"""
import pandas as pd
import re
from typing import Dict, List, Any
from datetime import datetime


class AFCONDataProcessor:
    """Process and clean AFCON match data"""
    
    @staticmethod
    def camel_to_snake(name: str) -> str:
        """Convert camelCase to snake_case"""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
        return s2.lower()
    
    @staticmethod
    def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame column names to snake_case"""
        df = df.copy()
        df.columns = [AFCONDataProcessor.camel_to_snake(c) for c in df.columns]
        return df
    
    @staticmethod
    def enforce_numeric(df: pd.DataFrame, exclude: set = None) -> pd.DataFrame:
        """Convert applicable columns to numeric types"""
        if exclude is None:
            exclude = set()
        
        df = df.copy()
        for col in df.columns:
            if col not in exclude:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    
    def process_match_summary(self, data: Dict[str, Any], event_id: str) -> Dict[str, pd.DataFrame]:
        """
        Process ESPN match summary into structured DataFrames
        
        Args:
            data: Raw JSON data from ESPN API
            event_id: Match event ID
            
        Returns:
            Dictionary of DataFrames: fact_match, fact_team_match, fact_goals, dim_team
        """
        comp = data["header"]["competitions"][0]
        
        # Fact Match
        fact_match = self._create_fact_match(data, comp, event_id)
        
        # Fact Team Match (with boxscore stats)
        fact_team_match = self._create_fact_team_match(data, comp, event_id)
        
        # Fact Goals
        fact_goals = self._create_fact_goals(comp, event_id)
        
        # Dim Team
        dim_team = self._create_dim_team(comp)
        
        return {
            "fact_match": fact_match,
            "fact_team_match": fact_team_match,
            "fact_goals": fact_goals,
            "dim_team": dim_team
        }
    
    def _create_fact_match(self, data: Dict, comp: Dict, event_id: str) -> pd.DataFrame:
        """Create fact_match DataFrame"""
        return pd.DataFrame([{
            "match_id": int(data["header"]["id"]),
            "date_utc": pd.to_datetime(comp["date"]),
            "season": data["header"]["season"]["year"],
            "competition": data["header"]["season"]["name"],
            "group_name": comp.get("groups", {}).get("name"),
            "status": comp["status"]["type"]["description"],
            "neutral_site": comp["neutralSite"],
            "venue_available": comp["boxscoreAvailable"]
        }])
    
    def _create_fact_team_match(self, data: Dict, comp: Dict, event_id: str) -> pd.DataFrame:
        """Create fact_team_match DataFrame with boxscore stats"""
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
        
        # Merge boxscore stats if available
        if "boxscore" in data and "teams" in data["boxscore"]:
            boxscore_df = self._extract_boxscore_stats(data["boxscore"], event_id)
            if not boxscore_df.empty:
                fact_team_match = fact_team_match.merge(
                    boxscore_df,
                    on=["match_id", "team_id"],
                    how="left"
                )
        
        # Add analytical features
        fact_team_match = self._add_analytical_features(fact_team_match)
        
        return fact_team_match
    
    def _extract_boxscore_stats(self, boxscore: Dict, event_id: str) -> pd.DataFrame:
        """Extract statistics from boxscore"""
        boxscore_rows = []
        
        for t in boxscore["teams"]:
            row = {
                "match_id": int(event_id),
                "team_id": int(t["team"]["id"])
            }
            for stat in t.get("statistics", []):
                row[stat["name"]] = stat["displayValue"]
            boxscore_rows.append(row)
        
        df = pd.DataFrame(boxscore_rows)
        if not df.empty:
            df = self.normalize_columns(df)
            df = self.enforce_numeric(df, exclude={"match_id", "team_id"})
        
        return df
    
    def _create_fact_goals(self, comp: Dict, event_id: str) -> pd.DataFrame:
        """Create fact_goals DataFrame"""
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
        
        return pd.DataFrame(goal_rows)
    
    def _create_dim_team(self, comp: Dict) -> pd.DataFrame:
        """Create dim_team DataFrame"""
        teams = []
        for t in comp["competitors"]:
            teams.append({
                "team_id": int(t["team"]["id"]),
                "team_name": t["team"]["displayName"],
                "abbreviation": t["team"]["abbreviation"],
                "country": t["team"]["location"],
                "color": t["team"]["color"]
            })
        
        return pd.DataFrame(teams).drop_duplicates()
    
    def _add_analytical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add calculated analytical features"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # Goal difference
        if "score" in df.columns:
            df["goal_difference"] = (
                df["score"] - 
                df.groupby("match_id")["score"].transform("max")
            )
        
        # Goal efficiency and domination index
        required_cols = {"shots_on_target", "total_shots", "possession_pct", "pass_pct", "score"}
        if required_cols.issubset(df.columns):
            df["goal_efficiency"] = df["score"] / df["shots_on_target"].replace(0, 1)
            df["domination_index"] = (
                0.4 * df["possession_pct"] +
                0.3 * df["pass_pct"] +
                0.3 * df["shots_on_target"]
            )
        
        return df
