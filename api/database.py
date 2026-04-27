import sqlite3
import json
import os
from collections import defaultdict, Counter

# ── JSON Fallback for deployment ──────────────────
ANALYTICS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "results", "analytics"
)

def _load_cached(filename: str):
    """Load pre-computed analytics JSON if DB unavailable."""
    path = os.path.join(ANALYTICS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "news.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _db_has_data() -> bool:
    try:
        conn = get_conn()
        count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False

def init_db():
    """Ensures all required columns exist."""
    try:
        conn = get_conn()
        cols = [row[1] for row in conn.execute("PRAGMA table_info(articles)")]
        if "sentiment" not in cols:
            conn.execute("ALTER TABLE articles ADD COLUMN sentiment TEXT")
            conn.commit()
        conn.close()
    except Exception:
        pass

init_db()


# ── Overview ──────────────────────────────────────
def get_overview():
    if not _db_has_data():
        return _load_cached("overview.json") or {}
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
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
    if not _db_has_data():
        return _load_cached("crawl_history.json") or []
    conn = get_conn()
    rows = conn.execute("""
        SELECT crawled_at, SUM(articles_found) as found, SUM(articles_new) as new
        FROM crawl_log
        GROUP BY crawled_at
        ORDER BY crawled_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [
        {"crawled_at": row["crawled_at"], "articles_found": row["found"], "articles_new": row["new"]}
        for row in rows
    ]


# ── Articles per Day ──────────────────────────────
def get_articles_per_day():
    if not _db_has_data():
        return _load_cached("articles_per_day.json") or []
    conn = get_conn()
    rows = conn.execute("""
        SELECT DATE(crawled_at) as date, COUNT(*) as count
        FROM articles
        GROUP BY DATE(crawled_at)
        ORDER BY date ASC
    """).fetchall()
    conn.close()
    return [{"date": row["date"], "count": row["count"]} for row in rows]


# ── Publishing Times ──────────────────────────────
def get_publishing_times():
    if not _db_has_data():
        return _load_cached("publishing_times.json") or []
    conn = get_conn()
    rows = conn.execute("""
        SELECT source, CAST(strftime('%H', crawled_at) AS INTEGER) as hour, COUNT(*) as count
        FROM articles
        WHERE crawled_at IS NOT NULL
        GROUP BY source, hour
        ORDER BY source, hour
    """).fetchall()
    conn.close()
    return [{"source": row["source"], "hour": row["hour"], "count": row["count"]} for row in rows]


# ── Weekday Activity ──────────────────────────────
def get_weekday_activity():
    if not _db_has_data():
        return _load_cached("weekday_activity.json") or []
    conn = get_conn()
    rows = conn.execute("""
        SELECT strftime('%w', crawled_at) as weekday, source, COUNT(*) as count
        FROM articles
        WHERE crawled_at IS NOT NULL
        GROUP BY weekday, source
        ORDER BY weekday, source
    """).fetchall()
    conn.close()
    weekday_names = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]
    return [
        {
            "weekday": weekday_names[int(row["weekday"])],
            "weekday_num": int(row["weekday"]),
            "source": row["source"],
            "count": row["count"]
        }
        for row in rows
    ]


# ── Articles per Day per Source ───────────────────
def get_articles_per_day_per_source():
    if not _db_has_data():
        return _load_cached("source_details.json") or []
    conn = get_conn()
    rows = conn.execute("""
        SELECT source, bias,
               COUNT(*) as total_articles,
               COUNT(DISTINCT DATE(crawled_at)) as active_days,
               ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT DATE(crawled_at)), 1) as avg_per_day
        FROM articles
        GROUP BY source
        ORDER BY avg_per_day DESC
    """).fetchall()
    conn.close()
    return [
        {
            "source": row["source"],
            "bias": row["bias"],
            "total_articles": row["total_articles"],
            "active_days": row["active_days"],
            "avg_per_day": row["avg_per_day"]
        }
        for row in rows
    ]


# ── Emotions per Bias (filtered) ──────────────────
def get_emotions_per_bias_filtered():
    if not _db_has_data():
        return _load_cached("emotions_per_bias.json") or {}
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT bias, emotion, COUNT(*) as count
            FROM articles
            WHERE emotion IS NOT NULL AND emotion != 'neutral'
            GROUP BY bias, emotion
            ORDER BY bias, count DESC
        """).fetchall()
        conn.close()
    except Exception:
        conn.close()
        return _load_cached("emotions_per_bias.json") or {}

    bias_data = defaultdict(list)
    bias_totals = defaultdict(int)
    for row in rows:
        bias_data[row["bias"]].append({"emotion": row["emotion"], "count": row["count"]})
        bias_totals[row["bias"]] += row["count"]

    return {
        bias: [
            {"emotion": e["emotion"], "count": e["count"],
             "pct": round(e["count"] * 100 / bias_totals[bias], 1)}
            for e in emotions[:5]
        ]
        for bias, emotions in bias_data.items()
    }


# ── Editorial Profile ─────────────────────────────
def get_source_editorial_profile(days_back: int = 14):
    if not _db_has_data():
        return _load_cached("editorial_profiles.json") or {}
    conn = get_conn()
    sources = {"taz": "left", "welt": "right-conservative", "junge_freiheit": "far-right"}
    result = {}
    for source_id, bias in sources.items():
        rows = conn.execute("""
            SELECT emotion FROM articles
            WHERE source_id = ? AND crawled_at >= datetime('now', ?)
            AND emotion IS NOT NULL AND emotion != 'neutral'
        """, (source_id, f'-{days_back} days')).fetchall()
        if not rows:
            result[source_id] = {"error": "No data"}
            continue
        total = len(rows)
        emotion_counts = Counter(row["emotion"] for row in rows)
        result[source_id] = {
            "source_id": source_id,
            "bias": bias,
            "total_non_neutral": total,
            "top_emotions": [
                {"emotion": e, "count": c, "pct": round(c * 100 / total, 1)}
                for e, c in emotion_counts.most_common(5)
            ]
        }
    conn.close()
    return result


# ── Trending Topics ───────────────────────────────
def get_trending_topics_from_db(days_back: int = 7, top_n: int = 20):
    cached = _load_cached("trending_topics.json")
    if cached:
        return cached[:top_n]
    return []


# ── Topic Analysis ────────────────────────────────
def get_topic_analysis(topic_id: str):
    """Loads cached topic analysis. Falls back to JSON file if DB empty."""
    if not _db_has_data():
        json_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "results", f"{topic_id}.json"
        )
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    conn = get_conn()
    try:
        row = conn.execute("""
            SELECT result_json, computed_at FROM analysis_results WHERE topic_id = ?
        """, (topic_id,)).fetchone()
        conn.close()
        if row:
            result = json.loads(row["result_json"])
            result["cached_at"] = row["computed_at"]
            return result
    except Exception:
        conn.close()

    json_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "results", f"{topic_id}.json"
    )
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None