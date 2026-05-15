import json
import os
from collections import defaultdict, Counter
import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("RAILWAY_DATABASE_URL") or os.getenv("DATABASE_URL")

# ── Static JSON files (pre-computed by ML pipeline) ─
ANALYTICS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "results", "analytics"
)
_RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "results")


def _load_cached(filename: str):
    path = os.path.join(ANALYTICS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL or RAILWAY_DATABASE_URL environment variable not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ── Overview ──────────────────────────────────────
def get_overview():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM articles")
        total = cur.fetchone()["count"]

        cur.execute(
            "SELECT source, COUNT(*) as count FROM articles GROUP BY source ORDER BY count DESC"
        )
        by_source = [{"source": r["source"], "count": r["count"]} for r in cur.fetchall()]

        cur.execute(
            "SELECT bias, COUNT(*) as count FROM articles GROUP BY bias ORDER BY count DESC"
        )
        by_bias = [{"bias": r["bias"], "count": r["count"]} for r in cur.fetchall()]

        try:
            cur.execute(
                "SELECT crawled_at, SUM(articles_new) as new FROM crawl_log GROUP BY crawled_at ORDER BY crawled_at DESC LIMIT 1"
            )
            last_crawl = cur.fetchone()
        except Exception:
            conn.rollback()
            last_crawl = None
        cur.close()
    finally:
        conn.close()

    return {
        "total_articles": int(total) if total is not None else 0,
        "by_source": [{"source": r["source"], "count": int(r["count"])} for r in by_source],
        "by_bias": [{"bias": r["bias"], "count": int(r["count"])} for r in by_bias],
        "last_crawl": {
            "crawled_at": str(last_crawl["crawled_at"]) if last_crawl else None,
            "new_articles": int(last_crawl["new"]) if last_crawl and last_crawl["new"] is not None else 0,
        },
    }


# ── Crawl History ─────────────────────────────────
def get_crawl_history(limit: int = 50):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                DATE_TRUNC('minute', crawled_at) AS crawled_at,
                SUM(articles_found) AS found,
                SUM(articles_new) AS new
            FROM crawl_log
            GROUP BY DATE_TRUNC('minute', crawled_at)
            ORDER BY crawled_at DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    return [
        {
            "crawled_at": str(r["crawled_at"]),
            "articles_found": int(r["found"]) if r["found"] is not None else 0,
            "articles_new": int(r["new"]) if r["new"] is not None else 0,
        }
        for r in rows
    ]


# ── Articles per Day ──────────────────────────────
def get_articles_per_day():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT crawled_at::date AS date, COUNT(*) AS count
            FROM articles
            GROUP BY crawled_at::date
            ORDER BY date ASC
        """)
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    return [{"date": str(r["date"]), "count": r["count"]} for r in rows]


# ── Publishing Times ──────────────────────────────
def get_publishing_times():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT source,
                   EXTRACT(HOUR FROM crawled_at)::integer AS hour,
                   COUNT(*) AS count
            FROM articles
            WHERE crawled_at IS NOT NULL
            GROUP BY source, hour
            ORDER BY source, hour
        """)
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    return [{"source": r["source"], "hour": r["hour"], "count": r["count"]} for r in rows]


# ── Weekday Activity ──────────────────────────────
def get_weekday_activity():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT EXTRACT(DOW FROM crawled_at)::integer AS weekday,
                   source,
                   COUNT(*) AS count
            FROM articles
            WHERE crawled_at IS NOT NULL
            GROUP BY weekday, source
            ORDER BY weekday, source
        """)
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    weekday_names = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]
    return [
        {
            "weekday": weekday_names[r["weekday"]],
            "weekday_num": r["weekday"],
            "source": r["source"],
            "count": r["count"],
        }
        for r in rows
    ]


# ── Articles per Day per Source ───────────────────
def get_articles_per_day_per_source():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT source, bias,
                   COUNT(*) AS total_articles,
                   COUNT(DISTINCT crawled_at::date) AS active_days,
                   ROUND(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT crawled_at::date), 0), 1) AS avg_per_day
            FROM articles
            GROUP BY source, bias
            ORDER BY avg_per_day DESC
        """)
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    return [
        {
            "source": r["source"],
            "bias": r["bias"],
            "total_articles": r["total_articles"],
            "active_days": r["active_days"],
            "avg_per_day": float(r["avg_per_day"]) if r["avg_per_day"] is not None else 0.0,
        }
        for r in rows
    ]


# ── Emotions per Bias (filtered) ──────────────────
def get_emotions_per_bias_filtered():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT bias, emotion, COUNT(*) AS count
            FROM articles
            WHERE emotion IS NOT NULL AND emotion != 'neutral'
            GROUP BY bias, emotion
            ORDER BY bias, count DESC
        """)
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    bias_data = defaultdict(list)
    bias_totals = defaultdict(int)
    for r in rows:
        bias_data[r["bias"]].append({"emotion": r["emotion"], "count": r["count"]})
        bias_totals[r["bias"]] += r["count"]

    return {
        bias: [
            {
                "emotion": e["emotion"],
                "count": e["count"],
                "pct": round(e["count"] * 100 / bias_totals[bias], 1),
            }
            for e in emotions[:5]
        ]
        for bias, emotions in bias_data.items()
    }


# ── Editorial Profile ─────────────────────────────
def get_source_editorial_profile(days_back: int = 14):
    sources = {"taz": "left", "welt": "right-conservative", "junge_freiheit": "far-right"}
    conn = get_conn()
    try:
        cur = conn.cursor()
        result = {}
        for source_id, bias in sources.items():
            cur.execute("""
                SELECT emotion FROM articles
                WHERE source_id = %s
                  AND crawled_at >= NOW() - (%s * INTERVAL '1 day')
                  AND emotion IS NOT NULL AND emotion != 'neutral'
            """, (source_id, days_back))
            rows = cur.fetchall()
            if not rows:
                result[source_id] = {"error": "No data"}
                continue
            total = len(rows)
            emotion_counts = Counter(r["emotion"] for r in rows)
            result[source_id] = {
                "source_id": source_id,
                "bias": bias,
                "total_non_neutral": total,
                "top_emotions": [
                    {"emotion": e, "count": c, "pct": round(c * 100 / total, 1)}
                    for e, c in emotion_counts.most_common(5)
                ],
            }
        cur.close()
    finally:
        conn.close()

    return result


# ── Trending Topics ───────────────────────────────
def get_trending_topics_from_db(days_back: int = 7, top_n: int = 20):
    cached = _load_cached("trending_topics.json")
    if cached:
        if isinstance(cached, dict) and ("deutschland" in cached or "international" in cached):
            return cached
        if isinstance(cached, list):
            return {"deutschland": cached[:top_n], "international": cached[:top_n]}
    return {"deutschland": [], "international": []}


# ── Topic Analysis ────────────────────────────────
def get_topic_analysis(topic_id: str):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT result_json, computed_at FROM analysis_results WHERE topic_id = %s",
            (topic_id,),
        )
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()

    if row:
        result = json.loads(row["result_json"])
        result["cached_at"] = str(row["computed_at"])
        return result

    json_path = os.path.join(_RESULTS_DIR, f"{topic_id}.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ── Manifesto Results ─────────────────────────────
def get_manifesto_year(year: int):
    path = os.path.join(_RESULTS_DIR, f"manifestos_{year}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_historical_analysis():
    path = os.path.join(_RESULTS_DIR, "historical_analysis.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_category_distribution(year: int):
    path = os.path.join(_RESULTS_DIR, f"category_distribution_{year}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_manifesto_analysis():
    path = os.path.join(_RESULTS_DIR, "manifesto_analysis.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
