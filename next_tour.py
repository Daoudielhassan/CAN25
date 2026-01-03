import requests
from datetime import datetime

NEWS_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/caf.nations/news"

def fetch_afcon_news(limit=10):
    r = requests.get(NEWS_URL, timeout=10)
    r.raise_for_status()
    data = r.json()

    news_items = []
    for article in data.get("articles", [])[:limit]:
        published = article.get("published")
        if published:
            published = datetime.fromisoformat(
                published.replace("Z", "+00:00")
            )

        news_items.append({
            "headline": article.get("headline"),
            "summary": article.get("description"),
            "author": article.get("byline"),
            "published_at": published,
            "url": article.get("links", {}).get("web", {}).get("href")
        })

    return news_items


if __name__ == "__main__":
    news = fetch_afcon_news()

    for n in news:
        print(f"\n📰 {n['headline']}")
        print(f"   {n['summary']}")
        print(f"   {n['url']}")
