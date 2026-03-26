import os
import sys
import json
import re
import sqlite3
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from news_collector import NEWS_SOURCES, fetch_rss, fetch_tagesschau, strip_html

# ── DB Setup ──────────────────────────────────────
DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "news.db"
)

def init_db(db_path: str):
    """Creates the SQLite database and articles table if not exists."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id          TEXT PRIMARY KEY,
            title       TEXT,
            description TEXT,
            text        TEXT,
            source      TEXT,
            source_id   TEXT,
            bias        TEXT,
            url         TEXT,
            published_at TEXT,
            crawled_at  TEXT,
            topic_hints TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS crawl_log (
            crawled_at  TEXT,
            source_id   TEXT,
            articles_found   INTEGER,
            articles_new     INTEGER
        )
    """)
    conn.commit()
    conn.close()


def article_id(url: str, title: str) -> str:
    """Generates a stable unique ID from URL or title."""
    key = url if url else title
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def save_articles(conn: sqlite3.Connection, articles: list[dict]) -> int:
    """Inserts new articles, skips duplicates. Returns count of new inserts."""
    new_count = 0
    for article in articles:
        try:
            conn.execute("""
                INSERT INTO articles
                (id, title, description, text, source, source_id, bias,
                 url, published_at, crawled_at, topic_hints)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article["id"],
                article["title"],
                article["description"],
                article["text"],
                article["source"],
                article["source_id"],
                article["bias"],
                article["url"],
                article["published_at"],
                datetime.utcnow().isoformat(),
                json.dumps(article.get("topic_hints", []))
            ))
            new_count += 1
        except sqlite3.IntegrityError:
            # Duplicate — skip silently
            pass
    conn.commit()
    return new_count


def detect_topic_hints(text: str) -> list[str]:
    """
    Detects which topics an article is relevant to
    based on keyword matching.
    """
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from config import TOPICS

    text_lower = text.lower()
    hints = []

    for topic_id, topic in TOPICS.items():
        keywords = topic.get("newsapi_keywords", [])
        if any(kw.lower() in text_lower for kw in keywords):
            hints.append(topic_id)

    return hints


# ── Main Crawler ──────────────────────────────────
def crawl(db_path: str = DB_PATH):
    """
    Crawls all 11 RSS sources, saves new articles to SQLite.
    Skips duplicates automatically via PRIMARY KEY constraint.
    """
    init_db(db_path)
    conn = sqlite3.connect(db_path)

    crawled_at = datetime.utcnow().isoformat()
    total_new = 0
    total_found = 0

    print(f"\n🦞 ConsensusAgent RSS Crawler")
    print(f"   Started: {crawled_at}")
    print(f"   DB: {db_path}\n")

    for source_id, source in NEWS_SOURCES.items():
        try:
            print(f"  Fetching {source['label']}...")

            if source_id == "tagesschau":
                # Use general news endpoint - no search, just latest articles
                headers = {"User-Agent": "ConsensusAgent/1.0 (research project)"}
                response = requests.get(
        "https://www.tagesschau.de/api2u/news",
        headers=headers,
        timeout=10
    )
                response.raise_for_status()
                data = response.json()
                raw_items = []
                for article in data.get("news", []):
                    raw_items.append({
                      "title": article.get("title", "").strip(),
                      "description": article.get("firstSenetence", "").strip(),
                      "url": article.get("shareURL", ""),
                      "published_at": article.get("date", "")
                      })
            else:
                raw_items = fetch_rss(source["url"])
            # Normalize
            articles = []
            for i, item in enumerate(raw_items):
                text = " ".join(filter(None, [
                    item["title"],
                    item["description"]
                ])).strip()

                if len(text) < 20:
                    continue

                art_id = article_id(item["url"], item["title"])
                topic_hints = detect_topic_hints(text)

                articles.append({
                    "id": art_id,
                    "title": item["title"],
                    "description": item["description"],
                    "text": text,
                    "source": source["label"],
                    "source_id": source_id,
                    "bias": source["bias"],
                    "url": item["url"],
                    "published_at": item["published_at"],
                    "topic_hints": topic_hints
                })

            new_count = save_articles(conn, articles)
            total_found += len(articles)
            total_new += new_count

            # Log
            conn.execute("""
                INSERT INTO crawl_log
                (crawled_at, source_id, articles_found, articles_new)
                VALUES (?, ?, ?, ?)
            """, (crawled_at, source_id, len(articles), new_count))
            conn.commit()

            print(f"    → {len(articles)} found, {new_count} new")

        except Exception as e:
            print(f"    ⚠ {source['label']} failed: {e}")
            continue

    conn.close()

    print(f"\n✅ Crawl complete")
    print(f"   Total found:  {total_found}")
    print(f"   Total new:    {total_new}")

    # Write summary for GitHub Actions step output
    summary_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "last_crawl.json"
    )
    with open(summary_path, "w") as f:
        json.dump({
            "crawled_at": crawled_at,
            "total_found": total_found,
            "total_new": total_new
        }, f, indent=2)


if __name__ == "__main__":
    crawl()