"""
db_setup.py — Creates the PostgreSQL schema for Diskursraum.

Idempotent — safe to run multiple times without side effects.

Usage:
    RAILWAY_DATABASE_URL=postgresql://... python crew/tools/media/db_setup.py
"""

import os
import sys
import psycopg2

DATABASE_URL = os.getenv("RAILWAY_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: RAILWAY_DATABASE_URL or DATABASE_URL environment variable not set.")
    sys.exit(1)


def run():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()

    print("Setting up schema on Railway PostgreSQL...")

    # ── Extension ──────────────────────────────────
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    print("  [OK] vector extension")

    # ── articles ───────────────────────────────────
    # id: SERIAL replaces SQLite's MD5-hash TEXT id.
    # url: UNIQUE — this is the natural deduplication key used by the crawler.
    # published_at: kept as TEXT — RSS pubDate formats vary too much to parse reliably.
    # embedding: vector(768) for jinaai/jina-embeddings-v2-base-de output dimensions.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id             SERIAL PRIMARY KEY,
            title          TEXT NOT NULL,
            description    TEXT,
            text           TEXT,
            source         TEXT NOT NULL,
            source_id      TEXT NOT NULL,
            bias           TEXT,
            url            TEXT UNIQUE NOT NULL,
            published_at   TEXT,
            crawled_at     TIMESTAMP DEFAULT NOW(),
            word_count     INTEGER DEFAULT 0,
            language       TEXT DEFAULT 'de',
            topic_hints    TEXT DEFAULT '[]',
            embedding      vector(768),
            sentiment      TEXT,
            emotion        TEXT,
            emotion_scores TEXT
        )
    """)
    print("  [OK] articles table")

    # ── crawl_log ──────────────────────────────────
    # Named crawl_log (not crawl_history) to match rss_crawler.py and database.py.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crawl_log (
            id             SERIAL PRIMARY KEY,
            crawled_at     TIMESTAMP DEFAULT NOW(),
            source_id      TEXT,
            articles_found INTEGER DEFAULT 0,
            articles_new   INTEGER DEFAULT 0
        )
    """)
    print("  [OK] crawl_log table")

    # ── analysis_results ───────────────────────────
    # Stores pre-computed Medienspiegel JSON per topic (bridging_scorer output).
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            topic_id      TEXT PRIMARY KEY,
            computed_at   TEXT,
            article_count INTEGER,
            result_json   TEXT
        )
    """)
    print("  [OK] analysis_results table")

    # ── topic_snapshots ────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS topic_snapshots (
            id            SERIAL PRIMARY KEY,
            discovered_at TIMESTAMP DEFAULT NOW(),
            topic         TEXT,
            relevance     REAL,
            article_count INTEGER,
            sample_titles TEXT,
            is_new        INTEGER DEFAULT 0,
            trend         TEXT DEFAULT 'stable'
        )
    """)
    print("  [OK] topic_snapshots table")

    # ── topic_trends ───────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS topic_trends (
            id            SERIAL PRIMARY KEY,
            date          TEXT,
            topic         TEXT,
            relevance     REAL,
            article_count INTEGER
        )
    """)
    print("  [OK] topic_trends table")

    # ── Standard indexes ───────────────────────────
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id)",
        "CREATE INDEX IF NOT EXISTS idx_articles_crawled_at ON articles(crawled_at)",
        "CREATE INDEX IF NOT EXISTS idx_articles_bias ON articles(bias)",
        "CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)",
        "CREATE INDEX IF NOT EXISTS idx_crawl_log_crawled_at ON crawl_log(crawled_at)",
    ]:
        cur.execute(idx_sql)
    print("  [OK] standard indexes")

    # ── Vector index ───────────────────────────────
    # HNSW instead of IVFFlat: works on empty tables (IVFFlat requires rows >= lists).
    # Better recall and no need to VACUUM/rebuild after large inserts.
    try:
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_embedding
                ON articles USING hnsw (embedding vector_cosine_ops)
        """)
        print("  [OK] vector index (hnsw, cosine)")
    except Exception as e:
        print(f"  [WARN] vector index skipped: {e}")
        print("         This is non-critical — similarity search still works via sequential scan.")

    # ── Validation ─────────────────────────────────
    print("\nValidating...")
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = [r[0] for r in cur.fetchall()]
    print(f"  Tables: {tables}")

    cur.execute("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'articles'
        ORDER BY indexname
    """)
    indexes = [r[0] for r in cur.fetchall()]
    print(f"  Indexes on articles: {indexes}")

    cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")
    ext = cur.fetchone()
    print(f"  pgvector: {ext}")

    cur.close()
    conn.close()
    print("\nSchema ready. Run db_migrate.py next.")


if __name__ == "__main__":
    run()
