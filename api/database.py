import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "news.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Ensures all required columns exist."""
    conn = get_conn()
    cols = [row[1] for row in conn.execute("PRAGMA table_info(articles)")]
    if "sentiment" not in cols:
        conn.execute("ALTER TABLE articles ADD COLUMN sentiment TEXT")
        conn.commit()
        print("✓ Migration: added sentiment column")
    conn.close()

init_db()

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
def get_emotions_per_bias_filtered():
    from collections import defaultdict
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT bias, emotion, COUNT(*) as count
            FROM articles
            WHERE emotion IS NOT NULL
            AND emotion != 'neutral'
            GROUP BY bias, emotion
            ORDER BY bias, count DESC
        """).fetchall()
        conn.close()
    except Exception:
        conn.close()
        return {}

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

  # ── Publishing Times ───────────────────────────────
def get_publishing_times():
    """Hour-of-day distribution per source."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            source,
            CAST(strftime('%H', crawled_at) AS INTEGER) as hour,
            COUNT(*) as count
        FROM articles
        WHERE crawled_at IS NOT NULL
        GROUP BY source, hour
        ORDER BY source, hour
    """).fetchall()
    conn.close()
    return [
        {"source": row["source"], "hour": row["hour"], "count": row["count"]}
        for row in rows
    ]


# ── Weekday Activity ──────────────────────────────
def get_weekday_activity():
    """Article count by weekday (0=Sunday, 6=Saturday)."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            strftime('%w', crawled_at) as weekday,
            source,
            COUNT(*) as count
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
    """Average articles per day per source."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            source,
            bias,
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
    """Sentiment distribution per source."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            source,
            bias,
            sentiment,
            COUNT(*) as count
        FROM articles
        WHERE sentiment IS NOT NULL
        GROUP BY source, sentiment
        ORDER BY source, sentiment
    """).fetchall()
    conn.close()
    return [
        {
            "source": row["source"],
            "bias": row["bias"],
            "sentiment": row["sentiment"],
            "count": row["count"]
        }
        for row in rows
    ]


# ── Sentiment per Bias ────────────────────────────
def get_sentiment_per_bias():
    """Sentiment distribution per bias group."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            bias,
            sentiment,
            COUNT(*) as count
        FROM articles
        WHERE sentiment IS NOT NULL
        GROUP BY bias, sentiment
        ORDER BY bias, sentiment
    """).fetchall()
    conn.close()
    return [
        {
            "bias": row["bias"],
            "sentiment": row["sentiment"],
            "count": row["count"]
        }
        for row in rows
    ]


# ── What occupies left vs right ───────────────────
def get_bias_focus(days_back: int = 7):
    """
    Top topic hints per bias group.
    Shows what left vs right media focuses on.
    """
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

    from collections import defaultdict, Counter
    import json

    bias_topics = defaultdict(Counter)
    for row in rows:
        try:
            hints = json.loads(row["topic_hints"])
            for hint in hints:
                bias_topics[row["bias"]][hint] += row["count"]
        except Exception:
            pass

    return {
        bias: [
            {"topic": topic, "count": count}
            for topic, count in counter.most_common(5)
        ]
        for bias, counter in bias_topics.items()
    }


# ── Neutrality Check ──────────────────────────────
def get_neutrality_check():
    """
    How neutral are the 'neutral' sources?
    Compares sentiment of neutral sources vs left/right.
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            bias,
            sentiment,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY bias), 1) as pct
        FROM articles
        WHERE sentiment IS NOT NULL
        GROUP BY bias, sentiment
        ORDER BY bias, sentiment
    """).fetchall()
    conn.close()
    return [
        {
            "bias": row["bias"],
            "sentiment": row["sentiment"],
            "count": row["count"],
            "percentage": row["pct"]
        }
        for row in rows
    ]

# ── Source Deep Dive ──────────────────────────────
def get_source_deep_dive(source_id: str, days_back: int = 30):
    """
    Deep analysis for a specific source.
    Top keywords, sentiment distribution, publishing patterns.
    """
    conn = get_conn()

    # Basic stats
    stats = conn.execute("""
        SELECT
            source,
            bias,
            COUNT(*) as total,
            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative,
            SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral,
            ROUND(AVG(word_count), 0) as avg_word_count
        FROM articles
        WHERE source_id = ?
        AND crawled_at >= datetime('now', ?)
    """, (source_id, f'-{days_back} days')).fetchone()

    # Recent titles sample
    titles = conn.execute("""
        SELECT title, sentiment, crawled_at
        FROM articles
        WHERE source_id = ?
        AND crawled_at >= datetime('now', ?)
        ORDER BY crawled_at DESC
        LIMIT 10
    """, (source_id, f'-{days_back} days')).fetchall()

    # Publishing hours
    hours = conn.execute("""
        SELECT
            CAST(strftime('%H', crawled_at) AS INTEGER) as hour,
            COUNT(*) as count
        FROM articles
        WHERE source_id = ?
        GROUP BY hour
        ORDER BY hour
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
            {
                "title": row["title"],
                "sentiment": row["sentiment"],
                "crawled_at": row["crawled_at"]
            }
            for row in titles
        ],
        "publishing_hours": [
            {"hour": row["hour"], "count": row["count"]}
            for row in hours
        ]
    }


# ── Left vs Right Comparison ──────────────────────
def get_left_right_comparison(days_back: int = 14):
    """
    Compares taz (left) vs Junge Freiheit (far-right) vs Die Welt (right-conservative).
    Sentiment, volume, publishing patterns.
    """
    conn = get_conn()

    sources = {
        "taz": "left",
        "junge_freiheit": "far-right",
        "welt": "right-conservative"
    }

    result = {}

    for source_id, bias in sources.items():
        rows = conn.execute("""
            SELECT
                title,
                text,
                sentiment,
                crawled_at,
                word_count
            FROM articles
            WHERE source_id = ?
            AND crawled_at >= datetime('now', ?)
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

        # TF-IDF top keywords
        texts = [row["text"] for row in rows if row["text"]]
        top_keywords = []
        if len(texts) >= 3:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                german_stopwords = [
                    "der", "die", "das", "den", "dem", "des", "ein", "eine",
                    "und", "oder", "aber", "nicht", "auch", "sich", "mit",
                    "von", "auf", "an", "in", "im", "ist", "sind", "war",
                    "hat", "haben", "wird", "werden", "bei", "nach", "aus",
                    "für", "zu", "als", "es", "er", "sie", "wir", "wie",
                    "dass", "so", "noch", "mehr", "nur", "schon", "jetzt",
                    "über", "durch", "bis", "seit", "vor", "unter", "the",
                    "and", "for", "that", "this", "with", "from", "have",
                ]
                vec = TfidfVectorizer(
                    max_features=200,
                    ngram_range=(1, 1),
                    min_df=2,
                    stop_words=german_stopwords
                )
                tfidf = vec.fit_transform(texts)
                scores = tfidf.mean(axis=0).A1
                names = vec.get_feature_names_out()
                top_idx = scores.argsort()[-15:][::-1]
                top_keywords = [
                    {"keyword": names[i], "score": round(float(scores[i]), 4)}
                    for i in top_idx
                    if len(names[i]) >= 4
                ]
            except Exception:
                pass

        result[source_id] = {
            "source_id": source_id,
            "bias": bias,
            "total_articles": total,
            "sentiment": sentiment_counts,
            "sentiment_pct": {
                k: round(v * 100 / total, 1) if total > 0 else 0
                for k, v in sentiment_counts.items()
            },
            "avg_word_count": round(
                sum(r["word_count"] or 0 for r in rows) / total, 0
            ),
            "top_keywords": top_keywords,
            "sample_titles": [row["title"] for row in rows[:5]]
        }

    conn.close()
    return result

# ── Emotions ──────────────────────────────────────
def get_emotions_per_bias():
    """Dominant emotion distribution per bias group."""
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
        return [
            {"bias": row["bias"], "emotion": row["emotion"], "count": row["count"]}
            for row in rows
        ]
    except Exception:
        conn.close()
        return []


def get_emotions_per_source():
    """Dominant emotion distribution per source."""
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
            {
                "source": row["source"],
                "bias": row["bias"],
                "emotion": row["emotion"],
                "count": row["count"]
            }
            for row in rows
        ]
    except Exception:
        conn.close()
        return []


def get_emotion_trends(days_back: int = 14):
    """Emotion distribution over time (by day)."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT
                DATE(crawled_at) as date,
                emotion,
                COUNT(*) as count
            FROM articles
            WHERE emotion IS NOT NULL
            AND crawled_at >= datetime('now', ?)
            GROUP BY date, emotion
            ORDER BY date ASC, count DESC
        """, (f'-{days_back} days',)).fetchall()
        conn.close()
        return [
            {"date": row["date"], "emotion": row["emotion"], "count": row["count"]}
            for row in rows
        ]
    except Exception:
        conn.close()
        return []


def get_left_right_emotions():
    """
    Emotion comparison: taz (left) vs Junge Freiheit (far-right) vs Welt (right-conservative).
    Shows what emotions dominate in each outlet's reporting.
    """
    conn = get_conn()
    sources = {
        "taz": "left",
        "junge_freiheit": "far-right",
        "welt": "right-conservative"
    }

    result = {}
    for source_id, bias in sources.items():
        try:
            rows = conn.execute("""
                SELECT emotion, COUNT(*) as count
                FROM articles
                WHERE source_id = ?
                AND emotion IS NOT NULL
                GROUP BY emotion
                ORDER BY count DESC
            """, (source_id,)).fetchall()

            total = sum(r["count"] for r in rows)
            if total == 0:
                continue

            result[source_id] = {
                "bias": bias,
                "total": total,
                "emotions": [
                    {
                        "emotion": row["emotion"],
                        "count": row["count"],
                        "pct": round(row["count"] * 100 / total, 1)
                    }
                    for row in rows[:8]
                ]
            }
        except Exception:
            continue

    conn.close()
    return result

# ── Topic Analysis ────────────────────────────────
def get_topic_analysis(topic_id: str):
    """
    Loads cached bridging analysis for a topic.
    Pre-computed by bridging_scorer.py via GitHub Actions.
    Returns None if not yet computed.
    """
    conn = get_conn()
    try:
        row = conn.execute("""
            SELECT result_json, computed_at, article_count
            FROM analysis_results
            WHERE topic_id = ?
        """, (topic_id,)).fetchone()
        conn.close()
        if not row:
            return None
        result = json.loads(row["result_json"])
        result["cached_at"] = row["computed_at"]
        return result
    except Exception:
        conn.close()
        return None


def get_all_topic_summaries():
    """
    Returns lightweight summaries for all cached topics.
    Used for Home page to show article counts per topic.
    """
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT topic_id, computed_at, article_count
            FROM analysis_results
            ORDER BY article_count DESC
        """).fetchall()
        conn.close()
        return [
            {
                "topic_id": row["topic_id"],
                "computed_at": row["computed_at"],
                "article_count": row["article_count"]
            }
            for row in rows
        ]
    except Exception:
        conn.close()
        return []

def get_source_editorial_profile(days_back: int = 14):
    """
    Returns emotional tone for taz, WELT, Junge Freiheit.
    Neutral excluded — not informative.
    """
    from collections import Counter

    conn = get_conn()
    sources = {
        "taz":            "left",
        "welt":           "right-conservative",
        "junge_freiheit": "far-right",
    }

    result = {}

    for source_id, bias in sources.items():
        rows = conn.execute("""
            SELECT emotion
            FROM articles
            WHERE source_id = ?
            AND crawled_at >= datetime('now', ?)
            AND emotion IS NOT NULL
            AND emotion != 'neutral'
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
                {
                    "emotion": emotion,
                    "count": count,
                    "pct": round(count * 100 / total, 1)
                }
                for emotion, count in emotion_counts.most_common(5)
            ]
        }

    conn.close()
    return result
