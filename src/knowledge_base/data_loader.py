"""
Data loader for historical AFCON data into vector store
"""
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document


class AFCONDataLoader:
    """Load and prepare historical AFCON data for embedding"""
    
    def __init__(self, data_dir: str = "./data/historical"):
        """
        Initialize data loader
        
        Args:
            data_dir: Directory containing historical CSV/JSON files
        """
        self.data_dir = Path(data_dir)
        self.match_mapping = self._load_match_mapping()
    
    def _load_match_mapping(self) -> Dict[int, str]:
        """Load match ID to team names mapping"""
        mapping = {}
        events_file = self.data_dir / "afcon_2025_all_events.csv"
        
        if events_file.exists():
            try:
                df = pd.read_csv(events_file)
                for _, row in df.iterrows():
                    mapping[int(row['event_id'])] = row['teams']
            except Exception as e:
                print(f"⚠️  Could not load match mapping: {e}")
        
        return mapping
    
    def load_csv_files(self) -> List[pd.DataFrame]:
        """Load all CSV files from data directory"""
        csv_files = list(self.data_dir.glob("*.csv"))
        dataframes = []
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                df.attrs['source'] = csv_file.name
                dataframes.append(df)
                print(f"✓ Loaded {csv_file.name}: {len(df)} rows")
            except Exception as e:
                print(f"✗ Error loading {csv_file.name}: {e}")
        
        return dataframes
    
    def create_documents_from_matches(self, df: pd.DataFrame) -> List[Document]:
        """
        Convert match data DataFrame to LangChain Documents
        
        Args:
            df: DataFrame with match data
            
        Returns:
            List of Document objects for embedding
        """
        documents = []
        
        for _, row in df.iterrows():
            # Create rich text description of the match
            content = self._format_match_content(row)
            
            # Metadata for filtering and context
            metadata = {
                "source": df.attrs.get('source', 'unknown'),
                "match_id": str(row.get('match_id', '')),
                "date": str(row.get('date', row.get('date_utc', ''))),
                "type": "match"
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def create_documents_from_teams(self, df: pd.DataFrame) -> List[Document]:
        """
        Convert team data DataFrame to LangChain Documents
        
        Args:
            df: DataFrame with team data
            
        Returns:
            List of Document objects for embedding
        """
        documents = []
        
        for _, row in df.iterrows():
            content = self._format_team_content(row)
            
            metadata = {
                "source": df.attrs.get('source', 'unknown'),
                "team_id": str(row.get('team_id', '')),
                "team_name": str(row.get('team_name', '')),
                "type": "team"
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def create_documents_from_goals(self, df: pd.DataFrame) -> List[Document]:
        """
        Convert goal data DataFrame to LangChain Documents
        
        Args:
            df: DataFrame with goal data
            
        Returns:
            List of Document objects for embedding
        """
        documents = []
        
        for _, row in df.iterrows():
            content = self._format_goal_content(row)
            
            metadata = {
                "source": df.attrs.get('source', 'unknown'),
                "match_id": str(row.get('match_id', '')),
                "scorer": str(row.get('scorer', '')),
                "type": "goal"
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def _format_match_content(self, row: pd.Series) -> str:
        """Format match row as readable text with full match context"""
        parts = []
        
        # Get match info from mapping
        if 'match_id' in row:
            match_id = int(row['match_id'])
            if match_id in self.match_mapping:
                parts.append(f"Match: {self.match_mapping[match_id]}")
            parts.append(f"Match ID: {match_id}")
        
        # Team and result info
        if 'team_name' in row:
            team_name = row['team_name']
            parts.append(f"Team: {team_name}")
            
            # Score and outcome
            if 'score' in row:
                score = row['score']
                parts.append(f"Goals Scored: {score}")
                
                # Winner/Loser info - only add if winner=True (actual win)
                if 'winner' in row and row['winner'] == True:
                    parts.append(f"Result: {team_name} WON the match")
        
        if 'date' in row or 'date_utc' in row:
            date = row.get('date', row.get('date_utc', ''))
            if pd.notna(date):
                parts.append(f"Date: {date}")
        
        if 'home_away' in row:
            parts.append(f"Venue: {row['home_away']}")
        
        if 'group_name' in row and pd.notna(row['group_name']):
            parts.append(f"Group: {row['group_name']}")
        
        # Key statistics
        stat_cols = [
            ('possession_pct', 'Possession'),
            ('total_shots', 'Shots'),
            ('shots_on_target', 'Shots on Target'),
            ('pass_pct', 'Pass Accuracy'),
            ('fouls_committed', 'Fouls'),
            ('yellow_cards', 'Yellow Cards'),
            ('red_cards', 'Red Cards')
        ]
        
        for col, label in stat_cols:
            if col in row and pd.notna(row[col]):
                value = row[col]
                if col.endswith('_pct'):
                    parts.append(f"{label}: {value}%")
                else:
                    parts.append(f"{label}: {value}")
        
        return " | ".join(parts)
    
    def _format_team_content(self, row: pd.Series) -> str:
        """Format team row as readable text"""
        parts = [f"Team: {row.get('team_name', 'Unknown')}"]
        
        if 'country' in row:
            parts.append(f"Country: {row['country']}")
        
        if 'abbreviation' in row:
            parts.append(f"Code: {row['abbreviation']}")
        
        return " | ".join(parts)
    
    def _format_goal_content(self, row: pd.Series) -> str:
        """Format goal row as readable text with match context"""
        parts = []
        
        # Add match context from mapping
        if 'match_id' in row:
            match_id = int(row['match_id'])
            if match_id in self.match_mapping:
                parts.append(f"Match: {self.match_mapping[match_id]}")
            parts.append(f"Match ID: {match_id}")
        
        # Add team info
        if 'team_id' in row:
            team_id = int(row['team_id'])
            if team_id == 2869:
                parts.append("Scoring Team: Morocco")
            else:
                parts.append(f"Team ID: {team_id}")
        
        if 'scorer' in row and pd.notna(row['scorer']):
            parts.append(f"Goal Scorer: {row['scorer']}")
        
        if 'minute' in row:
            parts.append(f"Time: {row['minute']}'")
        
        if 'assister' in row and pd.notna(row['assister']):
            parts.append(f"Assisted by: {row['assister']}")
        
        if 'penalty' in row and row['penalty']:
            parts.append("Type: Penalty kick")
        
        if 'own_goal' in row and row['own_goal']:
            parts.append("Type: Own Goal")
        
        return " | ".join(parts)
    
    def create_match_summary_documents(self, df: pd.DataFrame) -> List[Document]:
        """
        Create summary documents for complete matches with both teams
        
        Args:
            df: DataFrame with team_match data
            
        Returns:
            List of match summary documents
        """
        documents = []
        
        # Group by match_id to get both teams
        for match_id, group in df.groupby('match_id'):
            if len(group) != 2:
                continue  # Skip if not exactly 2 teams
            
            teams = group['team_name'].tolist()
            scores = group['score'].tolist()
            winners = group['winner'].tolist()
            
            # Determine match result
            match_name = self.match_mapping.get(int(match_id), f"{teams[0]} vs {teams[1]}")
            
            # Check if it's a draw
            if scores[0] == scores[1]:
                # It's a draw
                content = (
                    f"Match: {match_name} | "
                    f"Match ID: {match_id} | "
                    f"Final Score: {teams[0]} {scores[0]} - {scores[1]} {teams[1]} | "
                    f"Result: DRAW"
                )
                metadata = {
                    "source": "match_summary",
                    "match_id": str(match_id),
                    "result": "draw",
                    "type": "match_summary"
                }
            elif winners[0]:
                # Team 0 won
                winner_name = teams[0]
                loser_name = teams[1]
                winner_score = scores[0]
                loser_score = scores[1]
                content = (
                    f"Match: {match_name} | "
                    f"Match ID: {match_id} | "
                    f"Final Score: {teams[0]} {scores[0]} - {scores[1]} {teams[1]} | "
                    f"Winner: {winner_name} | "
                    f"Result: {winner_name} defeated {loser_name} {winner_score}-{loser_score}"
                )
                metadata = {
                    "source": "match_summary",
                    "match_id": str(match_id),
                    "winner": winner_name,
                    "loser": loser_name,
                    "type": "match_summary"
                }
            else:
                # Team 1 won
                winner_name = teams[1]
                loser_name = teams[0]
                winner_score = scores[1]
                loser_score = scores[0]
                content = (
                    f"Match: {match_name} | "
                    f"Match ID: {match_id} | "
                    f"Final Score: {teams[0]} {scores[0]} - {scores[1]} {teams[1]} | "
                    f"Winner: {winner_name} | "
                    f"Result: {winner_name} defeated {loser_name} {winner_score}-{loser_score}"
                )
                metadata = {
                    "source": "match_summary",
                    "match_id": str(match_id),
                    "winner": winner_name,
                    "loser": loser_name,
                    "type": "match_summary"
                }
            
            # Add date and group info for all cases
            date = group['date_utc'].iloc[0] if 'date_utc' in group.columns else None
            if pd.notna(date):
                content += f" | Date: {date}"
            
            group_name = group['group_name'].iloc[0] if 'group_name' in group.columns else None
            if pd.notna(group_name):
                content += f" | Group: {group_name}"
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def load_all_documents(self) -> List[Document]:
        """
        Load all data and convert to documents
        
        Returns:
            Complete list of documents for vector store
        """
        all_documents = []
        dataframes = self.load_csv_files()
        
        # Track team_match dataframes for standings calculation
        team_match_dfs = []
        goal_dfs = []
        
        for df in dataframes:
            source = df.attrs.get('source', '').lower()
            
            if 'team_match' in source:
                team_match_dfs.append(df)  # Save for standings
                # Create both detailed team docs and match summaries
                docs = self.create_documents_from_matches(df)
                all_documents.extend(docs)
                print(f"  → Created {len(docs)} match documents")
                
                # Create match summary documents
                summary_docs = self.create_match_summary_documents(df)
                all_documents.extend(summary_docs)
                print(f"  → Created {len(summary_docs)} match summary documents")
            
            elif 'match' in source and 'team_match' not in source:
                docs = self.create_documents_from_matches(df)
                all_documents.extend(docs)
                print(f"  → Created {len(docs)} match documents")
            
            elif 'team' in source and 'match' not in source:
                docs = self.create_documents_from_teams(df)
                all_documents.extend(docs)
                print(f"  → Created {len(docs)} team documents")
            
            elif 'goal' in source:
                goal_dfs.append(df)  # Save for top scorers
                docs = self.create_documents_from_goals(df)
                all_documents.extend(docs)
                print(f"  → Created {len(docs)} goal documents")
            
            elif 'news' in source:
                docs = self.create_documents_from_news(df)
                all_documents.extend(docs)
                print(f"  → Created {len(docs)} news documents")
            
            elif 'tournament_stats' in source:
                docs = self.create_tournament_statistics_documents(df)
                all_documents.extend(docs)
                print(f"  → Created {len(docs)} tournament statistics documents")
        
        # Create group standings documents
        if team_match_dfs:
            standings_docs = self.create_group_standings_documents(team_match_dfs)
            all_documents.extend(standings_docs)
            print(f"  → Created {len(standings_docs)} group standings documents")
        
        # Create top scorers documents
        if goal_dfs:
            scorers_docs = self.create_top_scorers_documents(goal_dfs)
            all_documents.extend(scorers_docs)
            print(f"  → Created {len(scorers_docs)} top scorers documents")
        
        # Create team aggregate statistics
        if team_match_dfs and goal_dfs:
            aggregate_docs = self.create_team_aggregate_statistics(team_match_dfs, goal_dfs)
            all_documents.extend(aggregate_docs)
            print(f"  → Created {len(aggregate_docs)} team aggregate statistics documents")
        
        print(f"\n📄 Total documents created: {len(all_documents)}")
        return all_documents
    
    def create_group_standings_documents(self, dfs: List[pd.DataFrame]) -> List[Document]:
        """
        Create documents for group standings and qualifications
        AFCON Rules: Top 2 from each group + best 4 third-placed teams qualify (16 teams total)
        
        Args:
            dfs: List of team_match DataFrames
            
        Returns:
            List of group standings documents
        """
        documents = []
        
        # Combine all team_match dataframes
        combined = pd.concat(dfs, ignore_index=True)
        
        # Get final points for each team in each group
        if 'group_name' not in combined.columns or 'points' not in combined.columns:
            return documents
        
        # Get groups
        groups = combined['group_name'].dropna().unique()
        
        # First pass: collect all third-placed teams
        all_third_place_teams = []
        group_standings = {}
        
        for group in groups:
            group_df = combined[combined['group_name'] == group]
            
            # IMPORTANT: Points column is cumulative, so we take MAX (final points) not SUM
            standings = []
            for team in group_df['team_name'].unique():
                team_data = group_df[group_df['team_name'] == team]
                
                # Get final cumulative points (max), total goals
                final_points = team_data['points'].max()  # Final cumulative points
                total_goals = team_data['score'].sum() if 'score' in team_data.columns else 0
                goals_conceded = team_data['opponent_score'].sum() if 'opponent_score' in team_data.columns else 0
                goal_difference = total_goals - goals_conceded
                
                standings.append({
                    'team_name': team,
                    'points': final_points,
                    'goals': total_goals,
                    'goals_conceded': goals_conceded,
                    'goal_difference': goal_difference,
                    'group': group
                })
            
            # Sort by points, then goal difference, then goals scored
            standings_df = pd.DataFrame(standings).sort_values(
                by=['points', 'goal_difference', 'goals'], 
                ascending=[False, False, False]
            ).reset_index(drop=True)
            
            standings_df['position'] = range(1, len(standings_df) + 1)
            group_standings[group] = standings_df
            
            # Collect third-placed team for best thirds comparison
            third_place = standings_df[standings_df['position'] == 3]
            if not third_place.empty:
                all_third_place_teams.append(third_place.iloc[0].to_dict())
        
        # Determine best 4 third-placed teams
        if all_third_place_teams:
            third_place_df = pd.DataFrame(all_third_place_teams).sort_values(
                by=['points', 'goal_difference', 'goals'],
                ascending=[False, False, False]
            ).reset_index(drop=True)
            best_thirds = set(third_place_df.head(4)['team_name'].tolist())
        else:
            best_thirds = set()
        
        # Second pass: create documents with correct qualification status
        for group in groups:
            standings_df = group_standings[group]
        # Second pass: create documents with correct qualification status
        for group in groups:
            standings_df = group_standings[group]
            
            # Create detailed standings document
            content_parts = [
                f"AFCON 2025 {group} Final Standings:"
            ]
            
            qualified_teams = []
            for idx, row in standings_df.iterrows():
                position = int(row['position'])
                team = row['team_name']
                points = int(row['points'])
                goals = int(row['goals'])
                goal_diff = int(row['goal_difference'])
                
                # Determine qualification status
                if position <= 2:
                    status = " (QUALIFIED - Top 2)"
                    qualified_teams.append(team)
                elif position == 3 and team in best_thirds:
                    status = " (QUALIFIED - Best 3rd place)"
                    qualified_teams.append(team)
                elif position == 3:
                    status = " (3rd place - Not qualified)"
                else:
                    status = " (Eliminated)"
                
                content_parts.append(
                    f"{position}. {team} - {points} points, {goals} goals, GD: {goal_diff:+d}{status}"
                )
            
            # Add qualification summary
            if qualified_teams:
                content_parts.append(
                    f"Teams qualified from {group}: {', '.join(qualified_teams)}"
                )
            
            content = " | ".join(content_parts)
            
            metadata = {
                "source": "group_standings",
                "group": group,
                "qualified_teams": ", ".join(qualified_teams),
                "type": "standings"
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def create_top_scorers_documents(self, dfs: List[pd.DataFrame]) -> List[Document]:
        """
        Create documents for top scorers in the tournament
        
        Args:
            dfs: List of goal DataFrames
            
        Returns:
            List of top scorer documents
        """
        documents = []
        
        # Combine all goal dataframes
        if not dfs:
            return documents
        
        combined = pd.concat(dfs, ignore_index=True)
        
        # Filter out own goals for top scorers
        if 'own_goal' in combined.columns:
            combined = combined[~combined['own_goal']]
        
        if 'scorer' not in combined.columns or combined.empty:
            return documents
        
        # Count goals per player
        scorer_counts = combined['scorer'].value_counts().reset_index()
        scorer_counts.columns = ['player', 'goals']
        
        # Team ID to name mapping (common AFCON teams)
        team_id_map = {
            2869: "Morocco", 2849: "Mali", 1740: "Tunisia", 3444: "Nigeria",
            1835: "Egypt", 3468: "Senegal", 1560: "Algeria", 1557: "Ivory Coast",
            1536: "Cameroon", 1611: "Burkina Faso", 2032: "South Africa",
            1580: "Congo DR", 2060: "Tanzania", 1843: "Mozambique", 1582: "Benin",
            2055: "Sudan", 4277: "Zambia", 2856: "Comoros", 1558: "Angola",
            2172: "Zimbabwe", 2050: "Uganda", 2861: "Gabon", 1581: "Botswana",
            1833: "Equatorial Guinea"
        }
        
        # Get team info for each scorer
        scorer_teams = {}
        for _, row in combined.iterrows():
            if pd.notna(row.get('scorer')):
                scorer = row['scorer']
                if scorer not in scorer_teams and 'team_id' in row:
                    team_id = int(row['team_id'])
                    scorer_teams[scorer] = team_id_map.get(team_id, f"Team {team_id}")
        
        # Create overall top scorers document
        top_10 = scorer_counts.head(10)
        content_parts = ["AFCON 2025 Top Scorers:"]
        
        for idx, row in top_10.iterrows():
            rank = idx + 1
            player = row['player']
            goals = int(row['goals'])
            team = scorer_teams.get(player, 'Unknown')
            
            content_parts.append(f"{rank}. {player} ({team}) - {goals} goals")
        
        content = " | ".join(content_parts)
        
        metadata = {
            "source": "top_scorers",
            "type": "statistics",
            "stat_type": "top_scorers"
        }
        
        documents.append(Document(page_content=content, metadata=metadata))
        
        # Create individual documents for top 5 scorers with their goals details
        for idx, row in scorer_counts.head(5).iterrows():
            player = row['player']
            player_goals = combined[combined['scorer'] == player]
            
            content_parts = [f"Top Scorer: {player}"]
            content_parts.append(f"Total Goals: {int(row['goals'])}")
            
            if player in scorer_teams:
                content_parts.append(f"Team: {scorer_teams[player]}")
            
            # Add goals breakdown
            content_parts.append("Goals scored:")
            for _, goal in player_goals.iterrows():
                goal_desc = f"Goal "
                if 'match_id' in goal and goal['match_id'] in self.match_mapping:
                    goal_desc += f"in {self.match_mapping[goal['match_id']]} "
                if 'minute' in goal:
                    goal_desc += f"at {goal['minute']}'"
                if 'penalty' in goal and goal['penalty']:
                    goal_desc += " (Penalty)"
                content_parts.append(goal_desc)
            
            content = " | ".join(content_parts)
            
            metadata = {
                "source": "player_stats",
                "type": "statistics",
                "player_name": player,
                "stat_type": "goals"
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def create_tournament_statistics_documents(self, df: pd.DataFrame) -> List[Document]:
        """
        Create documents from tournament-wide statistics
        
        Args:
            df: DataFrame with tournament statistics
            
        Returns:
            List of tournament statistics documents
        """
        documents = []
        
        if df.empty:
            return documents
        
        # Create discipline statistics document (cards)
        if 'yellowCards' in df.columns or 'redCards' in df.columns:
            content_parts = ["AFCON 2025 Discipline Statistics:"]
            
            # Most yellow cards
            if 'yellowCards' in df.columns:
                top_yellow = df.nlargest(5, 'yellowCards')[['team_name', 'yellowCards']]
                content_parts.append("\nMost Yellow Cards:")
                for idx, row in top_yellow.iterrows():
                    if row['yellowCards'] > 0:
                        content_parts.append(f"  {row['team_name']}: {int(row['yellowCards'])} yellow cards")
            
            # Most red cards
            if 'redCards' in df.columns:
                top_red = df.nlargest(5, 'redCards')[['team_name', 'redCards']]
                content_parts.append("\nMost Red Cards:")
                for idx, row in top_red.iterrows():
                    if row['redCards'] > 0:
                        content_parts.append(f"  {row['team_name']}: {int(row['redCards'])} red cards")
            
            # Fairplay ranking (fewest cards)
            if 'yellowCards' in df.columns and 'redCards' in df.columns:
                df['total_cards'] = df['yellowCards'].fillna(0) + (df['redCards'].fillna(0) * 3)
                fairplay = df.nsmallest(5, 'total_cards')[['team_name', 'yellowCards', 'redCards', 'total_cards']]
                content_parts.append("\nFair Play Ranking (Fewest Cards):")
                for idx, row in fairplay.iterrows():
                    yellow = int(row['yellowCards']) if pd.notna(row['yellowCards']) else 0
                    red = int(row['redCards']) if pd.notna(row['redCards']) else 0
                    total = row['total_cards']
                    content_parts.append(
                        f"  {row['team_name']}: {yellow} yellow, "
                        f"{red} red (Total: {total:.0f})"
                    )
            
            content = " | ".join(content_parts)
            
            metadata = {
                "source": "tournament_stats",
                "type": "statistics",
                "stat_type": "discipline"
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def create_team_aggregate_statistics(self, match_dfs: List[pd.DataFrame], goal_dfs: List[pd.DataFrame]) -> List[Document]:
        """
        Create aggregated statistics documents for each team across all their matches
        
        Args:
            match_dfs: List of team_match DataFrames
            goal_dfs: List of goal DataFrames
            
        Returns:
            List of aggregated team statistics documents
        """
        documents = []
        
        if not match_dfs:
            return documents
        
        # Combine all match data
        combined_matches = pd.concat(match_dfs, ignore_index=True)
        
        # Combine all goal data
        combined_goals = pd.concat(goal_dfs, ignore_index=True) if goal_dfs else pd.DataFrame()
        
        # Get unique teams
        teams = combined_matches['team_name'].unique()
        
        for team in teams:
            # Get all matches for this team
            team_matches = combined_matches[combined_matches['team_name'] == team]
            
            if team_matches.empty:
                continue
            
            # Calculate statistics
            total_matches = len(team_matches)
            total_goals = team_matches['score'].fillna(0).sum()
            total_goals_conceded = team_matches['opponent_score'].fillna(0).sum() if 'opponent_score' in team_matches.columns else 0
            wins = (team_matches['winner'] == True).sum()
            losses = (team_matches['winner'] == False).sum()
            draws = total_matches - wins - losses
            
            # Get goals by this team's players
            team_goals_detailed = []
            if not combined_goals.empty and 'team_id' in combined_goals.columns and 'team_id' in team_matches.columns:
                team_id = team_matches['team_id'].iloc[0]
                team_goal_data = combined_goals[combined_goals['team_id'] == team_id]
                
                if not team_goal_data.empty:
                    # Count goals by scorer
                    if 'scorer' in team_goal_data.columns:
                        scorers = team_goal_data['scorer'].value_counts()
                        for scorer, count in scorers.head(5).items():
                            team_goals_detailed.append(f"{scorer} ({int(count)} goals)")
            
            # Create comprehensive statistics document
            content_parts = [f"AFCON 2025 Complete Statistics for {team}:"]
            content_parts.append(f"\nOverall Record:")
            content_parts.append(f"  Matches Played: {total_matches}")
            content_parts.append(f"  Wins: {wins}, Draws: {draws}, Losses: {losses}")
            content_parts.append(f"  Goals Scored: {int(total_goals)}")
            content_parts.append(f"  Goals Conceded: {int(total_goals_conceded)}")
            content_parts.append(f"  Goal Difference: {int(total_goals - total_goals_conceded):+d}")
            
            if team_goals_detailed:
                content_parts.append(f"\nTop Scorers:")
                for scorer_info in team_goals_detailed:
                    content_parts.append(f"  {scorer_info}")
            
            # Add match results
            content_parts.append(f"\nMatch Results:")
            for _, match in team_matches.iterrows():
                match_info = f"  "
                if match['match_id'] in self.match_mapping:
                    match_info += f"{self.match_mapping[match['match_id']]}: "
                
                score = int(match['score']) if pd.notna(match['score']) else 0
                opp_score = int(match.get('opponent_score', 0)) if pd.notna(match.get('opponent_score')) else 0
                
                result = "Won" if match['winner'] else ("Drew" if score == opp_score else "Lost")
                match_info += f"{result} ({score}-{opp_score})"
                
                if 'group_name' in match and pd.notna(match['group_name']):
                    match_info += f" [{match['group_name']}]"
                
                content_parts.append(match_info)
            
            content = " | ".join(content_parts)
            
            metadata = {
                "source": "team_aggregate_stats",
                "type": "statistics",
                "team_name": team,
                "stat_type": "aggregate"
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def create_documents_from_news(self, df: pd.DataFrame) -> List[Document]:
        """
        Create documents from news articles
        
        Args:
            df: DataFrame with news data
            
        Returns:
            List of news documents
        """
        documents = []
        
        for _, row in df.iterrows():
            # Create news content
            parts = []
            
            if 'headline' in row and pd.notna(row['headline']):
                parts.append(f"Headline: {row['headline']}")
            
            if 'description' in row and pd.notna(row['description']):
                parts.append(f"Summary: {row['description']}")
            
            if 'author' in row and pd.notna(row['author']):
                parts.append(f"Author: {row['author']}")
            
            if 'published_at' in row and pd.notna(row['published_at']):
                parts.append(f"Published: {row['published_at']}")
            
            if 'category' in row and pd.notna(row['category']):
                parts.append(f"Category: {row['category']}")
            
            content = " | ".join(parts)
            
            metadata = {
                "source": "afcon_news",
                "type": "news",
                "headline": str(row.get('headline', '')),
                "published": str(row.get('published_at', '')),
                "url": str(row.get('url', ''))
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
