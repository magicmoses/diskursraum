from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database
import time

app = FastAPI(title="Diskursraum API", version="1.0.0")

# ── CORS — allow React frontend ───────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


# ── Analytics Endpoints ───────────────────────────
@app.get("/stats/overview")
def overview():
    return database.get_overview()


@app.get("/stats/crawl-history")
def crawl_history():
    return database.get_crawl_history()


@app.get("/stats/timeline")
def timeline():
    return database.get_timeline()


@app.get("/stats/topics")
def topics():
    return database.get_topic_distribution()


@app.get("/stats/articles-per-day")
def articles_per_day():
    return database.get_articles_per_day()


@app.get("/stats/bias-over-time")
def bias_over_time():
    return database.get_bias_over_time()

_trending_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 3600  # 1 Stunde

@app.get("/topics/trending")
def trending_topics(days_back: int = 7, top_n: int = 20):
    global _trending_cache
    now = time.time()
    if _trending_cache["data"] and (now - _trending_cache["timestamp"]) < CACHE_TTL:
        return _trending_cache["data"]
    result = database.get_trending_topics_from_db(days_back=days_back, top_n=top_n)
    _trending_cache = {"data": result, "timestamp": now}
    return result

@app.get("/stats/publishing-times")
def publishing_times():
    return database.get_publishing_times()

@app.get("/stats/weekday-activity")
def weekday_activity():
    return database.get_weekday_activity()

@app.get("/stats/source-details")
def source_details():
    return database.get_articles_per_day_per_source()

@app.get("/stats/bias-focus")
def bias_focus(days_back: int = 7):
    return database.get_bias_focus(days_back)

@app.get("/stats/source-deep-dive/{source_id}")
def source_deep_dive(source_id: str, days_back: int = 30):
    return database.get_source_deep_dive(source_id, days_back)

@app.get("/stats/emotions-per-source")
def emotions_per_source():
    return database.get_emotions_per_source()

@app.get("/stats/emotion-trends")
def emotion_trends(days_back: int = 14):
    return database.get_emotion_trends(days_back)

@app.get("/stats/left-right-emotions")
def left_right_emotions():
    return database.get_left_right_emotions()

@app.get("/topic/{topic_id}")
def get_topic(topic_id: str):
    result = database.get_topic_analysis(topic_id)
    if not result:
        return {"error": f"No cached analysis for '{topic_id}'. Run bridging_scorer.py first."}
    return result

@app.get("/topics/summaries")
def topic_summaries():
    return database.get_all_topic_summaries()

@app.get("/stats/editorial-profiles")
def editorial_profiles(days_back: int = 14):
    return database.get_source_editorial_profile(days_back)

@app.get("/stats/emotions-per-bias")
def emotions_per_bias():
    return database.get_emotions_per_bias_filtered()