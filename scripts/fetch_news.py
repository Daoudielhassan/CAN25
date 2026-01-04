"""
Fetch AFCON news from ESPN and save to dataset
"""
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

NEWS_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/caf.nations/news"
OUTPUT_DIR = Path("data/historical")

def fetch_afcon_news(limit=50):
    """Fetch AFCON news articles from ESPN API"""
    print("[LOADING] Fetching AFCON news from ESPN...")
    
    try:
        r = requests.get(NEWS_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[ERROR] Error fetching news: {e}")
        return []

    news_items = []
    for article in data.get("articles", [])[:limit]:
        published = article.get("published")
        if published:
            try:
                published = datetime.fromisoformat(
                    published.replace("Z", "+00:00")
                )
            except:
                published = None

        news_items.append({
            "headline": article.get("headline", ""),
            "description": article.get("description", ""),
            "author": article.get("byline", ""),
            "published_at": published.isoformat() if published else "",
            "url": article.get("links", {}).get("web", {}).get("href", ""),
            "category": ", ".join(c.get("description", "") for c in article.get("categories", [])),
            "type": article.get("type", "")
        })

    print(f"[OK] Fetched {len(news_items)} news articles")
    return news_items


def save_news_to_csv(news_items):
    """Save news to CSV file"""
    if not news_items:
        print("[ERROR] No news items to save")
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame(news_items)
    output_file = OUTPUT_DIR / "afcon_news.csv"
    df.to_csv(output_file, index=False)
    
    print(f"[OK] Saved news to {output_file}")
    print(f"  Total articles: {len(df)}")


def main():
    """Main execution"""
    print("=" * 60)
    print("AFCON News Fetcher")
    print("=" * 60)
    print()
    
    # Fetch news
    news = fetch_afcon_news(limit=50)
    
    # Save to CSV
    if news:
        save_news_to_csv(news)
        
        # Display sample
        print("\n[NEWS] Latest Headlines:")
        for item in news[:5]:
            print(f"  • {item['headline']}")
    
    print("\n" + "=" * 60)
    print("[OK] News fetch complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
