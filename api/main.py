import json
import os
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import date

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import database
import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload ChromaDB client + embedding model before the first request."""
    import asyncio
    import frag_nach as _fn
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _fn.warmup)
    yield


app = FastAPI(title="Diskursraum API", version="1.0.0", lifespan=lifespan)

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

@app.get("/manifesto-analysis")
def get_manifesto_analysis():
    result = database.get_manifesto_analysis()
    if not result:
        return {"error": "No manifesto analysis available. Run: python analyze_historical.py --nlp"}
    return result


# ── Frag nach — Rate Limiting ─────────────────────
_session_counter: dict = {}
_daily_ip_counter: defaultdict = defaultdict(int)
_ip_reset_day = date.today()
_SESSION_LIMIT = 10
_IP_DAILY_LIMIT = 50


def _check_ip_limit(ip: str) -> bool:
    global _daily_ip_counter, _ip_reset_day
    today = date.today()
    if today > _ip_reset_day:
        _daily_ip_counter.clear()
        _ip_reset_day = today
    _daily_ip_counter[ip] += 1
    return _daily_ip_counter[ip] <= _IP_DAILY_LIMIT


# ── Frag nach — Models ────────────────────────────
class DeepDiveRequest(BaseModel):
    query: str
    parties: list = []
    years: list = []
    session_id: str


# ── Frag nach — LLM Streaming ─────────────────────
_SYSTEM_PROMPT = (
    "Du bist ein neutraler politischer Analyst der Bundestagswahlprogramme "
    "deutscher Parteien analysiert. Antworte sachlich, ausgewogen und "
    "ausschließlich auf Basis der bereitgestellten Programmauszüge. "
    "Antworte auf Deutsch. Erfinde keine Informationen. "
    "Falls die Auszüge die Frage nicht beantworten können, sage das klar."
)
_USER_TEMPLATE = (
    "Frage: {query}\n\n"
    "Auszüge:\n{context}\n\n"
    "Antworte direkt in 2-3 Sätzen. Keine Einleitung. "
    "Partei und Jahr in Klammern nennen, z.B. (CDU/CSU 2021). "
    "Nur auf Basis der Auszüge — nichts erfinden."
)


async def _stream_llm(query: str, chunks: list):
    from frag_nach import format_chunks

    context = format_chunks(chunks)
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _USER_TEMPLATE.format(query=query, context=context)},
    ]

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=groq_key)
            stream = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.3,
                max_tokens=400,
                stream=True,
            )
            async for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
            return
        except Exception:
            pass

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=anthropic_key)
            async with client.messages.stream(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _USER_TEMPLATE.format(query=query, context=context)}],
            ) as stream:
                async for text in stream.text_stream:
                    yield f"data: {json.dumps({'token': text})}\n\n"
            yield "data: [DONE]\n\n"
            return
        except Exception:
            pass

    yield f"data: {json.dumps({'token': 'Kein LLM-Dienst verfügbar.'})}\n\n"
    yield "data: [DONE]\n\n"


# ── Frag nach — Query Intent Extraction ──────────
import re as _re

_PARTY_ALIASES = {
    "cdu/csu": "cdu_csu", "cdu": "cdu_csu", "csu": "cdu_csu", "union": "cdu_csu",
    "spd": "spd", "sozialdemokraten": "spd", "sozialdemokrat": "spd",
    "grünen": "gruene", "grüne": "gruene", "gruene": "gruene", "bündnis 90": "gruene", "bündnis": "gruene",
    "fdp": "fdp", "liberale": "fdp", "liberalen": "fdp",
    "afd": "afd", "alternative für deutschland": "afd",
    "linke": "linke", "linken": "linke", "pds": "linke",
}
_YEAR_RE = _re.compile(r"\b(2005|2009|2013|2017|2021|2025)\b")
_QUESTION_RE = _re.compile(
    r"\b(was|wie|warum|wann|wo|wer|welche[rns]?|sagt|denkt|meint|steht|"
    r"positioniert|plant|will|fordert|h[äa]lt|findet|ist die|sind die)\b",
    _re.IGNORECASE,
)
_PARTY_NAME_RE = _re.compile(
    r"\b(cdu[/\s]?csu|cdu|csu|union|spd|sozialdemokraten?|"
    r"gr[üu]nen?|b[üu]ndnis\s*90|fdp|liberalen?|afd|alternative\s+f[üu]r\s+deutschland|"
    r"linken?|pds)\b",
    _re.IGNORECASE,
)


def _rewrite_query(query: str) -> str:
    """Strip question structure and party/year noise for cleaner topic embedding."""
    q = _YEAR_RE.sub("", query)
    q = _PARTY_NAME_RE.sub("", q)
    q = _QUESTION_RE.sub("", q)
    q = _re.sub(r"\s+", " ", q).strip(" ?.,")
    return q if len(q) > 3 else query


def _extract_intent(query: str, parties: list, years: list):
    """Detect party/year from free-text query when no explicit filters are set."""
    lower = query.lower()
    auto_parties, auto_years = [], []

    if not parties:
        for alias, pid in _PARTY_ALIASES.items():
            if alias in lower and pid not in auto_parties:
                auto_parties.append(pid)

    if not years:
        auto_years = [int(m) for m in _YEAR_RE.findall(query)]

    clean = _rewrite_query(query)
    return clean, auto_parties or parties, auto_years or years


# ── Frag nach — Endpoints ─────────────────────────
@app.get("/frag-nach/search")
async def search_manifestos(
    query: str,
    parties: str = "all",
    years: str = "all",
    limit: int = 10,
):
    import frag_nach
    parties_list = [] if parties == "all" else [p.strip() for p in parties.split(",")]
    years_list = frag_nach.AVAILABLE_YEARS if years == "all" else [int(y) for y in years.split(",")]
    limit = max(1, min(limit, 30))

    clean_query, eff_parties, eff_years = _extract_intent(query, parties_list, years_list)

    try:
        results = await frag_nach.search(clean_query, eff_years, eff_parties, limit)
        return {"results": results, "query": query, "detected_filters": {"parties": eff_parties, "years": eff_years}, "total": len(results)}
    except Exception as e:
        return {"error": str(e), "results": [], "query": query, "total": 0}


@app.post("/frag-nach/deep-dive")
async def deep_dive_manifestos(request: DeepDiveRequest, req: Request):
    import frag_nach

    ip = req.client.host if req.client else "unknown"
    if not _check_ip_limit(ip):
        return {"error": "rate_limit_ip", "message": "Tägliches IP-Limit erreicht"}

    sid = request.session_id
    if _session_counter.get(sid, 0) >= _SESSION_LIMIT:
        return {"error": "rate_limit", "message": "Maximal 10 Deep-Dives pro Session"}
    _session_counter[sid] = _session_counter.get(sid, 0) + 1

    parties_list = [str(p) for p in request.parties] if request.parties else []
    years_list = [int(y) for y in request.years] if request.years else []

    clean_query, eff_parties, eff_years = _extract_intent(request.query, parties_list, years_list)
    if not eff_years:
        eff_years = frag_nach.AVAILABLE_YEARS

    try:
        chunks = await frag_nach.search(clean_query, eff_years, eff_parties, limit=10)
    except Exception as e:
        return {"error": str(e)}

    if not chunks:
        async def _empty():
            yield f"data: {json.dumps({'token': 'Keine relevanten Auszüge gefunden.'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_empty(), media_type="text/event-stream")

    return StreamingResponse(
        _stream_llm(request.query, chunks),
        media_type="text/event-stream",
    )