import os
import sys
import json
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "news.db"
)


def init_topic_tables(db_path: str = DB_PATH):
    """Creates topic discovery tables if not exist."""
    conn = sqlite3.connect(db_path)

    # Discovered topics per run
    conn.execute("""
        CREATE TABLE IF NOT EXISTS topic_snapshots (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            discovered_at TEXT,
            topic        TEXT,
            relevance    REAL,
            article_count INTEGER,
            sample_titles TEXT,
            is_new       INTEGER DEFAULT 0,
            trend        TEXT DEFAULT 'stable'
        )
    """)

    # Topic trends over time
    conn.execute("""
        CREATE TABLE IF NOT EXISTS topic_trends (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT,
            topic        TEXT,
            relevance    REAL,
            article_count INTEGER
        )
    """)

    conn.commit()
    conn.close()
    print("✓ Topic tables initialized")


def save_snapshot(topics: list[dict], db_path: str = DB_PATH):
    """Saves a topic discovery snapshot."""
    conn = sqlite3.connect(db_path)
    discovered_at = datetime.utcnow().isoformat()

    for topic in topics:
        conn.execute("""
            INSERT INTO topic_snapshots
            (discovered_at, topic, relevance, article_count,
             sample_titles, is_new, trend)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            discovered_at,
            topic["topic"],
            topic["relevance"],
            topic["article_count"],
            json.dumps(topic.get("sample_titles", [])),
            1 if topic.get("is_new") else 0,
            topic.get("trend", "stable")
        ))

        # Also write to trends table for time series
        conn.execute("""
            INSERT INTO topic_trends (date, topic, relevance, article_count)
            VALUES (?, ?, ?, ?)
        """, (
            discovered_at[:10],
            topic["topic"],
            topic["relevance"],
            topic["article_count"]
        ))

    conn.commit()
    conn.close()


def get_previous_topics(days_back: int = 3, db_path: str = DB_PATH) -> list[str]:
    """Returns topics discovered in the last N days."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT DISTINCT topic FROM topic_snapshots
        WHERE discovered_at >= datetime('now', ?)
        ORDER BY relevance DESC
    """, (f'-{days_back} days',)).fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_topic_trends(limit: int = 30, db_path: str = DB_PATH) -> list[dict]:
    """Returns topic trend data for the frontend."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT date, topic, relevance, article_count
        FROM topic_trends
        ORDER BY date DESC, relevance DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [
        {
            "date": row[0],
            "topic": row[1],
            "relevance": row[2],
            "article_count": row[3]
        }
        for row in rows
    ]


if __name__ == "__main__":
    init_topic_tables()