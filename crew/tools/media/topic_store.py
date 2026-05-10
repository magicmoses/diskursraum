import os
import json
from datetime import datetime
import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("RAILWAY_DATABASE_URL") or os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL or RAILWAY_DATABASE_URL not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def save_snapshot(topics: list[dict]):
    """Saves a topic discovery snapshot."""
    conn = get_conn()
    cur = conn.cursor()
    discovered_at = datetime.utcnow().isoformat()

    for topic in topics:
        cur.execute("""
            INSERT INTO topic_snapshots
                (discovered_at, topic, relevance, article_count,
                 sample_titles, is_new, trend)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            discovered_at,
            topic["topic"],
            topic["relevance"],
            topic["article_count"],
            json.dumps(topic.get("sample_titles", [])),
            1 if topic.get("is_new") else 0,
            topic.get("trend", "stable"),
        ))

        cur.execute("""
            INSERT INTO topic_trends (date, topic, relevance, article_count)
            VALUES (%s, %s, %s, %s)
        """, (
            discovered_at[:10],
            topic["topic"],
            topic["relevance"],
            topic["article_count"],
        ))

    conn.commit()
    cur.close()
    conn.close()


def get_previous_topics(days_back: int = 3) -> list[str]:
    """Returns topics discovered in the last N days."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT topic FROM topic_snapshots
        WHERE discovered_at >= NOW() - (%s * INTERVAL '1 day')
        ORDER BY topic
    """, (days_back,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r["topic"] for r in rows]


def get_topic_trends(limit: int = 30) -> list[dict]:
    """Returns topic trend data for the frontend."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT date, topic, relevance, article_count
        FROM topic_trends
        ORDER BY date DESC, relevance DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "date": r["date"],
            "topic": r["topic"],
            "relevance": r["relevance"],
            "article_count": r["article_count"],
        }
        for r in rows
    ]
