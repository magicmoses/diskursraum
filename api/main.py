from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database

app = FastAPI(title="ConsensusAgent API", version="1.0.0")

# ── CORS — allow React frontend ───────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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

@app.get("/topics/trending")
def trending_topics(days_back: int = 7, top_n: int = 20):
    return database.get_trending_topics_from_db(days_back=days_back, top_n=top_n)