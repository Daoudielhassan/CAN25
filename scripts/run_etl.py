"""
Script to run ETL on a match and save to CSV
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.live_data import ESPNAPIClient, AFCONDataProcessor


def main():
    """Run ETL for a match"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_etl.py <event_id>")
        print()
        print("Example: python scripts/run_etl.py 732133")
        return
    
    event_id = sys.argv[1]
    
    print("=" * 60)
    print(f"ETL Process - Event {event_id}")
    print("=" * 60)
    print()
    
    # Fetch data
    print("📥 Fetching match data...")
    client = ESPNAPIClient()
    data = client.fetch_match_summary(event_id)
    
    if not data:
        print("❌ Failed to fetch match data")
        return
    
    print("✓ Data fetched successfully")
    print()
    
    # Process data
    print("🔄 Processing data...")
    processor = AFCONDataProcessor()
    dataframes = processor.process_match_summary(data, event_id)
    
    print("✓ Data processed successfully")
    print()
    
    # Save to CSV
    print("💾 Saving to CSV files...")
    output_prefix = f"afcon_{event_id}"
    
    for name, df in dataframes.items():
        filename = f"{output_prefix}_{name}.csv"
        df.to_csv(filename, index=False)
        print(f"   ✓ {filename} ({len(df)} rows)")
    
    print()
    print("=" * 60)
    print("✅ ETL Complete!")
    print("=" * 60)
    print()
    print("Files generated:")
    for name in dataframes.keys():
        print(f"  - {output_prefix}_{name}.csv")
    print()


if __name__ == "__main__":
    main()
