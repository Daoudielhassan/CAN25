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
                docs = self.create_documents_from_goals(df)
                all_documents.extend(docs)
                print(f"  → Created {len(docs)} goal documents")
            
            elif 'news' in source:
                docs = self.create_documents_from_news(df)
                all_documents.extend(docs)
                print(f"  → Created {len(docs)} news documents")
        
        # Create group standings documents
        if team_match_dfs:
            standings_docs = self.create_group_standings_documents(team_match_dfs)
            all_documents.extend(standings_docs)
            print(f"  → Created {len(standings_docs)} group standings documents")
        
        print(f"\n📄 Total documents created: {len(all_documents)}")
        return all_documents
    
    def create_group_standings_documents(self, dfs: List[pd.DataFrame]) -> List[Document]:
        """
        Create documents for group standings and qualifications
        
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
        
        for group in groups:
            group_df = combined[combined['group_name'] == group]
            
            # Get final standings (max points per team)
            standings = (
                group_df[['team_name', 'points', 'advance']]
                .groupby('team_name')
                .agg({'points': 'max', 'advance': 'any'})
                .sort_values('points', ascending=False)
                .reset_index()
            )
            
            # Create standings text
            content_parts = [f"Group: {group}", "Final Standings:"]
            
            qualified_teams = []
            for idx, row in standings.iterrows():
                rank = idx + 1
                team = row['team_name']
                points = row['points']
                advanced = row['advance']
                
                status = " (QUALIFIED)" if advanced else ""
                content_parts.append(f"{rank}. {team}: {points} points{status}")
                
                if advanced:
                    qualified_teams.append(team)
            
            # Add qualification summary
            if qualified_teams:
                content_parts.append(f"\nTeams that qualified from {group}: {', '.join(qualified_teams)}")
            
            content = " | ".join(content_parts)
            
            metadata = {
                "source": "group_standings",
                "group": group,
                "qualified_teams": ", ".join(qualified_teams),
                "type": "standings"
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
