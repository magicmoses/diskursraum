import os
import sys
import json
import re
import sqlite3
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ── Path setup — no crewai needed ─────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from topics import TOPICS
from news_collector import NEWS_SOURCES, fetch_rss, strip_html

# ── DB Setup ──────────────────────────────────────
DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "news.db"
)

def init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id           TEXT PRIMARY KEY,
            title        TEXT,
            description  TEXT,
            text         TEXT,
            source       TEXT,
            source_id    TEXT,
            bias         TEXT,
            url          TEXT,
            published_at TEXT,
            crawled_at   TEXT,
            word_count   INTEGER,
            language     TEXT DEFAULT 'de',
            topic_hints  TEXT DEFAULT '[]'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS crawl_log (
            crawled_at      TEXT,
            source_id       TEXT,
            articles_found  INTEGER,
            articles_new    INTEGER
        )
    """)
    conn.commit()
    conn.close()


def article_id(url: str, title: str) -> str:
    key = url if url else title
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def detect_topic_hints(text: str) -> list[str]:
    text_lower = text.lower()
    return [
        topic_id for topic_id, topic in TOPICS.items()
        if any(kw.lower() in text_lower for kw in topic.get("newsapi_keywords", []))
    ]


def save_articles(conn: sqlite3.Connection, articles: list[dict]) -> int:
    new_count = 0
    for article in articles:
        try:
            conn.execute("""
                INSERT INTO articles
                (id, title, description, text, source, source_id, bias,
                 url, published_at, crawled_at, word_count, language, topic_hints)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                len(article["text"].split()),
                article.get("language", "de"),
                json.dumps(article.get("topic_hints", []))
            ))
            new_count += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    return new_count


def fetch_tagesschau_news() -> list[dict]:
    """Fetches latest news from Tagesschau JSON API."""
    headers = {"User-Agent": "ConsensusAgent/1.0 (research project)"}
    response = requests.get(
        "https://www.tagesschau.de/api2u/news",
        headers=headers,
        timeout=10
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
            "language": "de"
        })
    return items


def crawl(db_path: str = DB_PATH):
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
                raw_items = fetch_tagesschau_news()
            else:
                raw_items = fetch_rss(source["url"])

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

                # DW publishes in multiple languages — detect English
                language = "en" if source_id == "dw" and any(
                    c.isascii() for c in text[:50]
                ) else "de"

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
                    "language": language,
                    "topic_hints": topic_hints
                })

            new_count = save_articles(conn, articles)
            total_found += len(articles)
            total_new += new_count

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