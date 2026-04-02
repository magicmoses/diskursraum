import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "news.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Overview ──────────────────────────────────────
def get_overview():
    conn = get_conn()

    total = conn.execute(
        "SELECT COUNT(*) FROM articles"
    ).fetchone()[0]

    by_source = [
        {"source": row["source"], "count": row["count"]}
        for row in conn.execute(
            "SELECT source, COUNT(*) as count FROM articles GROUP BY source ORDER BY count DESC"
        )
    ]

    by_bias = [
        {"bias": row["bias"], "count": row["count"]}
        for row in conn.execute(
            "SELECT bias, COUNT(*) as count FROM articles GROUP BY bias ORDER BY count DESC"
        )
    ]

    last_crawl = conn.execute(
        "SELECT crawled_at, SUM(articles_new) as new FROM crawl_log ORDER BY crawled_at DESC LIMIT 1"
    ).fetchone()

    conn.close()
    return {
        "total_articles": total,
        "by_source": by_source,
        "by_bias": by_bias,
        "last_crawl": {
            "crawled_at": last_crawl["crawled_at"] if last_crawl else None,
            "new_articles": last_crawl["new"] if last_crawl else 0
        }
    }


# ── Crawl History ─────────────────────────────────
def get_crawl_history(limit: int = 50):
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            crawled_at,
            SUM(articles_found) as found,
            SUM(articles_new) as new
        FROM crawl_log
        GROUP BY crawled_at
        ORDER BY crawled_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [
        {
            "crawled_at": row["crawled_at"],
            "articles_found": row["found"],
            "articles_new": row["new"]
        }
        for row in rows
    ]


# ── Timeline ──────────────────────────────────────
def get_timeline():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            DATE(crawled_at) as date,
            source,
            COUNT(*) as count
        FROM articles
        GROUP BY DATE(crawled_at), source
        ORDER BY date ASC
    """).fetchall()
    conn.close()
    return [
        {
            "date": row["date"],
            "source": row["source"],
            "count": row["count"]
        }
        for row in rows
    ]


# ── Topics ────────────────────────────────────────
def get_topic_distribution():
    conn = get_conn()
    rows = conn.execute(
        "SELECT topic_hints FROM articles WHERE topic_hints != '[]'"
    ).fetchall()
    conn.close()

    from collections import Counter
    all_hints = []
    for row in rows:
        all_hints += json.loads(row["topic_hints"])

    return [
        {"topic": topic, "count": count}
        for topic, count in Counter(all_hints).most_common()
    ]


# ── Articles per day ──────────────────────────────
def get_articles_per_day():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            DATE(crawled_at) as date,
            COUNT(*) as count
        FROM articles
        GROUP BY DATE(crawled_at)
        ORDER BY date ASC
    """).fetchall()
    conn.close()
    return [
        {"date": row["date"], "count": row["count"]}
        for row in rows
    ]


# ── Bias balance per day ──────────────────────────
def get_bias_over_time():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            DATE(crawled_at) as date,
            bias,
            COUNT(*) as count
        FROM articles
        GROUP BY DATE(crawled_at), bias
        ORDER BY date ASC
    """).fetchall()
    conn.close()
    return [
        {
            "date": row["date"],
            "bias": row["bias"],
            "count": row["count"]
        }
        for row in rows
    ]

# ── Trending Topics ───────────────────────────────
def get_trending_topics_from_db(days_back: int = 7, top_n: int = 20):
    """
    Calls the clusterer's get_trending_topics function.
    Cached in DB for 6 hours to avoid repeated LLM calls.
    """
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "crew", "tools"))
    from clusterer import get_trending_topics

    return get_trending_topics(days_back=days_back, top_n=top_n)