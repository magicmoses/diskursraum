import sqlite3
import json
import os
from datetime import datetime
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
            print("✓ Migration: added sentiment column")
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


# ── Timeline ──────────────────────────────────────
def get_timeline():
    conn = get_conn()
    rows = conn.execute("""
        SELECT DATE(crawled_at) as date, source, COUNT(*) as count
        FROM articles
        GROUP BY DATE(crawled_at), source
        ORDER BY date ASC
    """).fetchall()
    conn.close()
    return [{"date": row["date"], "source": row["source"], "count": row["count"]} for row in rows]


# ── Topics ────────────────────────────────────────
def get_topic_distribution():
    conn = get_conn()
    rows = conn.execute("SELECT topic_hints FROM articles WHERE topic_hints != '[]'").fetchall()
    conn.close()
    all_hints = []
    for row in rows:
        all_hints += json.loads(row["topic_hints"])
    return [{"topic": t, "count": c} for t, c in Counter(all_hints).most_common()]


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


# ── Bias over Time ────────────────────────────────
def get_bias_over_time():
    conn = get_conn()
    rows = conn.execute("""
        SELECT DATE(crawled_at) as date, bias, COUNT(*) as count
        FROM articles
        GROUP BY DATE(crawled_at), bias
        ORDER BY date ASC
    """).fetchall()
    conn.close()
    return [{"date": row["date"], "bias": row["bias"], "count": row["count"]} for row in rows]


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


# ── Sentiment per Source ──────────────────────────
def get_sentiment_per_source():
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT source, bias, sentiment, COUNT(*) as count
            FROM articles
            WHERE sentiment IS NOT NULL
            GROUP BY source, sentiment
            ORDER BY source, sentiment
        """).fetchall()
        conn.close()
        return [
            {"source": row["source"], "bias": row["bias"], "sentiment": row["sentiment"], "count": row["count"]}
            for row in rows
        ]
    except Exception:
        conn.close()
        return []


# ── Sentiment per Bias ────────────────────────────
def get_sentiment_per_bias():
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT bias, sentiment, COUNT(*) as count
            FROM articles
            WHERE sentiment IS NOT NULL
            GROUP BY bias, sentiment
            ORDER BY bias, sentiment
        """).fetchall()
        conn.close()
        return [{"bias": row["bias"], "sentiment": row["sentiment"], "count": row["count"]} for row in rows]
    except Exception:
        conn.close()
        return []


# ── Bias Focus ────────────────────────────────────
def get_bias_focus(days_back: int = 7):
    conn = get_conn()
    rows = conn.execute("""
        SELECT bias, topic_hints, COUNT(*) as count
        FROM articles
        WHERE topic_hints != '[]'
        AND crawled_at >= datetime('now', ?)
        GROUP BY bias, topic_hints
        ORDER BY bias, count DESC
    """, (f'-{days_back} days',)).fetchall()
    conn.close()
    bias_topics = defaultdict(Counter)
    for row in rows:
        try:
            hints = json.loads(row["topic_hints"])
            for hint in hints:
                bias_topics[row["bias"]][hint] += row["count"]
        except Exception:
            pass
    return {
        bias: [{"topic": t, "count": c} for t, c in counter.most_common(5)]
        for bias, counter in bias_topics.items()
    }


# ── Neutrality Check ─────────────────────────────
def get_neutrality_check():
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT bias, sentiment, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY bias), 1) as pct
            FROM articles
            WHERE sentiment IS NOT NULL
            GROUP BY bias, sentiment
            ORDER BY bias, sentiment
        """).fetchall()
        conn.close()
        return [
            {"bias": row["bias"], "sentiment": row["sentiment"], "count": row["count"], "percentage": row["pct"]}
            for row in rows
        ]
    except Exception:
        conn.close()
        return []


# ── Source Deep Dive ──────────────────────────────
def get_source_deep_dive(source_id: str, days_back: int = 30):
    conn = get_conn()
    stats = conn.execute("""
        SELECT source, bias, COUNT(*) as total,
               SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
               SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative,
               SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral,
               ROUND(AVG(word_count), 0) as avg_word_count
        FROM articles
        WHERE source_id = ? AND crawled_at >= datetime('now', ?)
    """, (source_id, f'-{days_back} days')).fetchone()
    titles = conn.execute("""
        SELECT title, sentiment, crawled_at FROM articles
        WHERE source_id = ? AND crawled_at >= datetime('now', ?)
        ORDER BY crawled_at DESC LIMIT 10
    """, (source_id, f'-{days_back} days')).fetchall()
    hours = conn.execute("""
        SELECT CAST(strftime('%H', crawled_at) AS INTEGER) as hour, COUNT(*) as count
        FROM articles WHERE source_id = ?
        GROUP BY hour ORDER BY hour
    """, (source_id,)).fetchall()
    conn.close()
    if not stats or not stats["total"]:
        return {"error": f"No data for source_id '{source_id}'"}
    return {
        "source_id": source_id,
        "source": stats["source"],
        "bias": stats["bias"],
        "total_articles": stats["total"],
        "sentiment": {
            "positive": stats["positive"] or 0,
            "negative": stats["negative"] or 0,
            "neutral": stats["neutral"] or 0,
        },
        "avg_word_count": stats["avg_word_count"],
        "recent_titles": [
            {"title": r["title"], "sentiment": r["sentiment"], "crawled_at": r["crawled_at"]}
            for r in titles
        ],
        "publishing_hours": [{"hour": r["hour"], "count": r["count"]} for r in hours]
    }


# ── Left vs Right Comparison ──────────────────────
def get_left_right_comparison(days_back: int = 14):
    conn = get_conn()
    sources = {"taz": "left", "junge_freiheit": "far-right", "welt": "right-conservative"}
    result = {}
    for source_id, bias in sources.items():
        rows = conn.execute("""
            SELECT title, text, sentiment, crawled_at, word_count
            FROM articles
            WHERE source_id = ? AND crawled_at >= datetime('now', ?)
            ORDER BY crawled_at DESC
        """, (source_id, f'-{days_back} days')).fetchall()
        if not rows:
            result[source_id] = {"error": "No data"}
            continue
        total = len(rows)
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for row in rows:
            if row["sentiment"] in sentiment_counts:
                sentiment_counts[row["sentiment"]] += 1
        result[source_id] = {
            "source_id": source_id,
            "bias": bias,
            "total_articles": total,
            "sentiment": sentiment_counts,
            "sentiment_pct": {k: round(v * 100 / total, 1) if total > 0 else 0 for k, v in sentiment_counts.items()},
            "avg_word_count": round(sum(r["word_count"] or 0 for r in rows) / total, 0),
            "sample_titles": [row["title"] for row in rows[:5]]
        }
    conn.close()
    return result


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


# ── Emotions per Bias (raw) ───────────────────────
def get_emotions_per_bias():
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT bias, emotion, COUNT(*) as count
            FROM articles
            WHERE emotion IS NOT NULL
            GROUP BY bias, emotion
            ORDER BY bias, count DESC
        """).fetchall()
        conn.close()
        return [{"bias": row["bias"], "emotion": row["emotion"], "count": row["count"]} for row in rows]
    except Exception:
        conn.close()
        return []


# ── Emotions per Source ───────────────────────────
def get_emotions_per_source():
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT source, bias, emotion, COUNT(*) as count
            FROM articles
            WHERE emotion IS NOT NULL
            GROUP BY source, emotion
            ORDER BY source, count DESC
        """).fetchall()
        conn.close()
        return [
            {"source": row["source"], "bias": row["bias"], "emotion": row["emotion"], "count": row["count"]}
            for row in rows
        ]
    except Exception:
        conn.close()
        return []


# ── Emotion Trends ────────────────────────────────
def get_emotion_trends(days_back: int = 14):
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT DATE(crawled_at) as date, emotion, COUNT(*) as count
            FROM articles
            WHERE emotion IS NOT NULL AND crawled_at >= datetime('now', ?)
            GROUP BY date, emotion
            ORDER BY date ASC, count DESC
        """, (f'-{days_back} days',)).fetchall()
        conn.close()
        return [{"date": row["date"], "emotion": row["emotion"], "count": row["count"]} for row in rows]
    except Exception:
        conn.close()
        return []


# ── Left vs Right Emotions ────────────────────────
def get_left_right_emotions():
    conn = get_conn()
    sources = {"taz": "left", "junge_freiheit": "far-right", "welt": "right-conservative"}
    result = {}
    for source_id, bias in sources.items():
        try:
            rows = conn.execute("""
                SELECT emotion, COUNT(*) as count
                FROM articles
                WHERE source_id = ? AND emotion IS NOT NULL
                GROUP BY emotion ORDER BY count DESC
            """, (source_id,)).fetchall()
            total = sum(r["count"] for r in rows)
            if total == 0:
                continue
            result[source_id] = {
                "bias": bias,
                "total": total,
                "emotions": [
                    {"emotion": r["emotion"], "count": r["count"], "pct": round(r["count"] * 100 / total, 1)}
                    for r in rows[:8]
                ]
            }
        except Exception:
            continue
    conn.close()
    return result


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
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "crew", "tools"))
    from clusterer import get_trending_topics
    return get_trending_topics(days_back=days_back, top_n=top_n)


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

    # Fallback to JSON file
    json_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "results", f"{topic_id}.json"
    )
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ── Topic Summaries ───────────────────────────────
def get_all_topic_summaries():
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT topic_id, computed_at, article_count
            FROM analysis_results ORDER BY article_count DESC
        """).fetchall()
        conn.close()
        return [
            {"topic_id": row["topic_id"], "computed_at": row["computed_at"], "article_count": row["article_count"]}
            for row in rows
        ]
    except Exception:
        conn.close()
        return []