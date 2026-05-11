"""
frag_nach.py — Semantic manifesto search

Embedding:   intfloat/multilingual-e5-base
             ONNX backend if optimum[onnxruntime] is installed (3-5x faster),
             PyTorch fallback otherwise.
             Model is pre-baked into the Docker image via nixpacks.toml build step —
             no download on container start, load from disk only (~1-3s).
             warmup() is called at API startup so the first request is instant.

Retrieval:   pgvector (Railway PostgreSQL), manifesto_chunks table,
             all years queried in parallel via ThreadPoolExecutor.
             Seeded once locally via scripts/migrate_chroma_to_pg.py.

Caching:     LRU for embeddings (256 entries) and results (64 entries).

Latency after warmup:
  embed   ~20-40ms  (ONNX)   /  ~100-150ms (PyTorch)
  pg      ~10-30ms  (parallel, all 6 years, HNSW index)
  total   ~30-70ms  /  ~110-180ms  — well under 500ms target
"""

import asyncio
import hashlib
import os
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
AVAILABLE_YEARS = [2005, 2009, 2013, 2017, 2021, 2025]

_model_instance = None
_pg_pool = None
_executor = ThreadPoolExecutor(
    max_workers=len(AVAILABLE_YEARS),
    thread_name_prefix="pgvec",
)

# ── LRU caches ────────────────────────────────────
_embed_cache: OrderedDict = OrderedDict()
_result_cache: OrderedDict = OrderedDict()
_EMBED_CACHE_MAX = 256
_RESULT_CACHE_MAX = 64


def _lru_get(cache: OrderedDict, key: str):
    if key in cache:
        cache.move_to_end(key)
        return cache[key]
    return None


def _lru_set(cache: OrderedDict, key: str, value, max_size: int) -> None:
    cache[key] = value
    cache.move_to_end(key)
    if len(cache) > max_size:
        cache.popitem(last=False)


# ── Model ─────────────────────────────────────────
def _get_model():
    global _model_instance
    if _model_instance is None:
        from sentence_transformers import SentenceTransformer
        try:
            # model_O4.onnx — graph-optimised, pre-baked into image by nixpacks build
            _model_instance = SentenceTransformer(
                EMBEDDING_MODEL, backend="onnx",
                model_kwargs={"file_name": "onnx/model_O4.onnx"},
            )
        except Exception:
            _model_instance = SentenceTransformer(EMBEDDING_MODEL)
    return _model_instance


# ── DB Pool ───────────────────────────────────────
def _get_pool():
    global _pg_pool
    if _pg_pool is None:
        from psycopg2.pool import ThreadedConnectionPool
        url = os.getenv("RAILWAY_DATABASE_URL") or os.getenv("DATABASE_URL")
        _pg_pool = ThreadedConnectionPool(1, len(AVAILABLE_YEARS) + 2, dsn=url)
    return _pg_pool


def warmup() -> None:
    """
    Called once in FastAPI lifespan — before the first request.
    Opens DB connection pool and runs one encode pass to:
      - trigger ONNX runtime JIT compilation
      - warm BLAS thread pools (PyTorch path)
    so that real requests are served from warm state.
    """
    _get_pool()
    _get_model().encode(
        "query: Bundestagswahlprogramm Deutschland",
        normalize_embeddings=True,
    )


# ── Embedding ─────────────────────────────────────
def embed_query(text: str) -> list:
    key = hashlib.md5(text.encode()).hexdigest()
    cached = _lru_get(_embed_cache, key)
    if cached is not None:
        return cached
    vec = _get_model().encode(f"query: {text}", normalize_embeddings=True).tolist()
    _lru_set(_embed_cache, key, vec, _EMBED_CACHE_MAX)
    return vec


# ── pgvector ──────────────────────────────────────
def _query_one_year(year: int, qe: list, parties: list, n: int) -> list:
    """Single-year vector search against manifesto_chunks. Runs in thread pool."""
    import psycopg2.extras

    vec_str = "[" + ",".join(map(str, qe)) + "]"
    pool = _get_pool()
    conn = pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if parties:
            cur.execute(
                """
                SELECT chunk_text, party_id, party_name, year,
                       ROUND((1 - (embedding <=> %s::vector))::numeric, 4) AS relevance_score
                FROM manifesto_chunks
                WHERE year = %s AND party_id = ANY(%s)
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vec_str, year, parties, vec_str, n),
            )
        else:
            cur.execute(
                """
                SELECT chunk_text, party_id, party_name, year,
                       ROUND((1 - (embedding <=> %s::vector))::numeric, 4) AS relevance_score
                FROM manifesto_chunks
                WHERE year = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vec_str, year, vec_str, n),
            )
        rows = cur.fetchall()
        cur.close()
    except Exception:
        rows = []
    finally:
        pool.putconn(conn)

    return [
        {
            "text": r["chunk_text"],
            "party": r["party_name"],
            "party_id": r["party_id"],
            "year": r["year"],
            "relevance_score": float(r["relevance_score"]),
        }
        for r in rows
    ]


# ── Public search API ─────────────────────────────
async def search(query: str, years: list, parties: list, limit: int) -> list:
    """
    Embed → parallel pgvector query across year slices → rank.
    Result cache avoids redundant work for repeated queries.
    """
    cache_key = hashlib.md5(
        f"{query}|{'_'.join(map(str, sorted(years)))}|{'_'.join(sorted(parties))}".encode()
    ).hexdigest()
    cached = _lru_get(_result_cache, cache_key)
    if cached is not None:
        return cached

    loop = asyncio.get_running_loop()
    qe = await loop.run_in_executor(None, embed_query, query)

    n = min(limit, 10)
    tasks = [
        loop.run_in_executor(_executor, _query_one_year, yr, qe, parties, n)
        for yr in years
    ]
    batches = await asyncio.gather(*tasks)

    hits = [h for batch in batches for h in batch]
    hits.sort(key=lambda x: x["relevance_score"], reverse=True)
    result = hits[:limit]

    _lru_set(_result_cache, cache_key, result, _RESULT_CACHE_MAX)
    return result


def format_chunks(chunks: list) -> str:
    return "\n\n".join(
        f"[{c['party']}, {c['year']}]: {c['text']}" for c in chunks
    )
