from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database
import time

app = FastAPI(title="Diskursraum API", version="1.0.0")

# ── CORS ──────────────────────────────────────────
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

# ── Analytics ─────────────────────────────────────
@app.get("/stats/overview")
def overview():
    return database.get_overview()

@app.get("/stats/crawl-history")
def crawl_history():
    return database.get_crawl_history()

@app.get("/stats/articles-per-day")
def articles_per_day():
    return database.get_articles_per_day()

@app.get("/stats/publishing-times")
def publishing_times():
    return database.get_publishing_times()

@app.get("/stats/weekday-activity")
def weekday_activity():
    return database.get_weekday_activity()

@app.get("/stats/source-details")
def source_details():
    return database.get_articles_per_day_per_source()

@app.get("/stats/emotions-per-bias")
def emotions_per_bias():
    return database.get_emotions_per_bias_filtered()

@app.get("/stats/editorial-profiles")
def editorial_profiles(days_back: int = 14):
    return database.get_source_editorial_profile(days_back)

# ── Trending Topics ───────────────────────────────
_trending_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 3600

@app.get("/topics/trending")
def trending_topics(days_back: int = 7, top_n: int = 20):
    global _trending_cache
    now = time.time()
    if _trending_cache["data"] and (now - _trending_cache["timestamp"]) < CACHE_TTL:
        return _trending_cache["data"]
    result = database.get_trending_topics_from_db(days_back=days_back, top_n=top_n)
    _trending_cache = {"data": result, "timestamp": now}
    return result

# ── Topic Analysis ────────────────────────────────
@app.get("/topic/{topic_id}")
def get_topic(topic_id: str):
    result = database.get_topic_analysis(topic_id)
    if not result:
        return {"error": f"No cached analysis for '{topic_id}'."}
    return result

# ── Manifesto Analysis ────────────────────────────
VALID_MANIFESTO_YEARS = [2005, 2009, 2013, 2017, 2021, 2025]

@app.get("/manifestos/historical")
def get_historical():
    result = database.get_historical_analysis()
    if not result:
        return {"error": "No historical analysis available"}
    return result

@app.get("/manifestos/categories/{year}")
def get_manifesto_categories(year: int):
    if year not in VALID_MANIFESTO_YEARS:
        return {"error": f"Year {year} not available. Valid: {VALID_MANIFESTO_YEARS}"}
    result = database.get_category_distribution(year)
    if not result:
        return {"error": f"No category data for {year}"}
    return result

@app.get("/manifestos/{year}")
def get_manifesto(year: int):
    if year not in VALID_MANIFESTO_YEARS:
        return {"error": f"Year {year} not available. Valid: {VALID_MANIFESTO_YEARS}"}
    result = database.get_manifesto_year(year)
    if not result:
        return {"error": f"No manifesto data for {year}"}
    return result