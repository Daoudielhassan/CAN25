"""
Enhanced data loader with match context mapping
"""
import pandas as pd
from pathlib import Path

# Create match mapping from events data
data_dir = Path("./data/historical")
events_df = pd.read_csv(data_dir / "afcon_2025_all_events.csv")

# Create a dictionary mapping match_id to match info
match_mapping = {}
for _, row in events_df.iterrows():
    match_id = row['event_id']
    teams = row['teams']
    match_mapping[match_id] = teams

print("Match ID to Teams Mapping:")
print("=" * 60)
for match_id, teams in sorted(match_mapping.items()):
    print(f"{match_id}: {teams}")

# Save to a file for easy reference
output = data_dir / "match_mapping.txt"
with open(output, 'w') as f:
    for match_id, teams in sorted(match_mapping.items()):
        f.write(f"{match_id}|{teams}\n")

print(f"\n✓ Saved mapping to {output}")
