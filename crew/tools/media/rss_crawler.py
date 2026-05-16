import os
import sys
import json
import re
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import psycopg2
import psycopg2.extras

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from topics import TOPICS
from news_collector import NEWS_SOURCES, fetch_rss, strip_html

DATABASE_URL = os.getenv("RAILWAY_DATABASE_URL") or os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL or RAILWAY_DATABASE_URL not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def article_id(url: str, title: str) -> str:
    key = url if url else title
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def detect_topic_hints(text: str) -> list[str]:
    text_lower = text.lower()
    return [
        topic_id for topic_id, topic in TOPICS.items()
        if any(kw.lower() in text_lower for kw in topic.get("newsapi_keywords", []))
    ]


def save_articles(conn, articles: list[dict]) -> int:
    cur = conn.cursor()
    new_count = 0
    crawled_at = datetime.utcnow().isoformat()
    for article in articles:
        cur.execute("""
            INSERT INTO articles
                (title, description, text, source, source_id, bias,
                 url, published_at, crawled_at, word_count, language, topic_hints)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING
        """, (
            article["title"],
            article["description"],
            article["text"],
            article["source"],
            article["source_id"],
            article["bias"],
            article["url"],
            article["published_at"],
            crawled_at,
            len(article["text"].split()),
            article.get("language", "de"),
            json.dumps(article.get("topic_hints", [])),
        ))
        if cur.rowcount > 0:
            new_count += 1
    conn.commit()
    cur.close()
    return new_count


def fetch_tagesschau_news() -> list[dict]:
    headers = {"User-Agent": "Diskursraum/1.0 (research project)"}
    response = requests.get(
        "https://www.tagesschau.de/api2u/news",
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    items = []
    for article in data.get("news", []):
        items.append({
            "title": article.get("title", "").strip(),
            "description": article.get("firstSentence", "").strip(),
            "url": article.get("shareURL", ""),
            "published_at": article.get("date", ""),
            "language": "de",
        })
    return items


def crawl():
    conn = get_conn()
    crawled_at = datetime.utcnow().isoformat()
    total_new = 0
    total_found = 0

    print(f"\n Diskursraum RSS Crawler")
    print(f"   Started: {crawled_at}\n")

    cur = conn.cursor()
    for source_id, source in NEWS_SOURCES.items():
        try:
            print(f"  Fetching {source['label']}...")

            if source_id == "tagesschau":
                raw_items = fetch_tagesschau_news()
            else:
                raw_items = fetch_rss(source["url"])

            articles = []
            for item in raw_items:
                text = " ".join(filter(None, [item["title"], item["description"]])).strip()
                if len(text) < 20:
                    continue

                topic_hints = detect_topic_hints(text)
                language = "en" if source_id == "dw" and any(
                    c.isascii() for c in text[:50]
                ) else "de"

                articles.append({
                    "title": item["title"],
                    "description": item["description"],
                    "text": text,
                    "source": source["label"],
                    "source_id": source_id,
                    "bias": source["bias"],
                    "url": item["url"],
                    "published_at": item["published_at"],
                    "language": language,
                    "topic_hints": topic_hints,
                })

            new_count = save_articles(conn, articles)
            total_found += len(articles)
            total_new += new_count

            cur.execute("""
                INSERT INTO crawl_log (crawled_at, source_id, articles_found, articles_new)
                VALUES (%s, %s, %s, %s)
            """, (crawled_at, source_id, len(articles), new_count))
            conn.commit()

            print(f"    → {len(articles)} found, {new_count} new")

        except Exception as e:
            print(f"    ⚠ {source['label']} failed: {e}")
            continue

    cur.close()
    conn.close()

    print(f"\n✅ Crawl complete")
    print(f"   Total found:  {total_found}")
    print(f"   Total new:    {total_new}")

    summary_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "last_crawl.json"
    )
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump({
            "crawled_at": crawled_at,
            "total_found": total_found,
            "total_new": total_new,
        }, f, indent=2)


if __name__ == "__main__":
    crawl()
