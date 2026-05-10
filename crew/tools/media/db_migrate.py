"""
db_migrate.py — Migrates all data from SQLite (data/news.db) to Railway PostgreSQL.

Run db_setup.py first to create the schema.

Usage:
    RAILWAY_DATABASE_URL=postgresql://... python crew/tools/media/db_migrate.py
"""

import os
import sys
import json
import sqlite3
import pickle
import numpy as np
import psycopg2
import psycopg2.extras

SQLITE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "news.db"
)
DATABASE_URL = os.getenv("RAILWAY_DATABASE_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: RAILWAY_DATABASE_URL or DATABASE_URL environment variable not set.")
    sys.exit(1)

if not os.path.exists(SQLITE_PATH):
    print(f"ERROR: SQLite DB not found at {SQLITE_PATH}")
    sys.exit(1)

BATCH_SIZE = 500


def vec_to_str(arr: np.ndarray) -> str:
    """Formats a numpy array as a pgvector literal: '[0.1,0.2,...]'"""
    return "[" + ",".join(f"{x:.8f}" for x in arr) + "]"


def check_embedding_format(sqlite_conn) -> bool:
    """Inspects the first available embedding and confirms it's 768-dim float32."""
    print("\nChecking embedding format in SQLite...")
    row = sqlite_conn.execute(
        "SELECT id, embedding FROM articles WHERE embedding IS NOT NULL LIMIT 1"
    ).fetchone()

    if not row:
        print("  No embeddings found in SQLite — skipping format check.")
        return True

    blob = row[1]
    print(f"  BLOB size: {len(blob)} bytes")

    try:
        arr = pickle.loads(blob)
        print(f"  pickle.loads → numpy array, shape: {arr.shape}, dtype: {arr.dtype}")
        if arr.shape != (768,):
            print(f"  ERROR: Expected shape (768,) but got {arr.shape}. Stopping.")
            return False
        print("  Format confirmed: 768-dim float32 — ready to migrate.")
        return True
    except Exception as e:
        # Fallback: try raw float32 buffer
        try:
            arr = np.frombuffer(blob, dtype=np.float32)
            print(f"  np.frombuffer → shape: {arr.shape}")
            if arr.shape != (768,):
                print(f"  ERROR: Expected (768,) but got {arr.shape}. Stopping.")
                return False
            print("  Format confirmed (raw float32 buffer).")
            return True
        except Exception as e2:
            print(f"  ERROR: Cannot decode embedding — {e} / {e2}. Stopping.")
            return False


def load_embedding(blob) -> str | None:
    """Decodes a SQLite embedding BLOB to pgvector string. Returns None on failure."""
    if blob is None:
        return None
    try:
        arr = pickle.loads(blob)
        if arr.shape == (768,):
            return vec_to_str(arr.astype(np.float32))
    except Exception:
        pass
    try:
        arr = np.frombuffer(blob, dtype=np.float32)
        if arr.shape == (768,):
            return vec_to_str(arr)
    except Exception:
        pass
    return None


def migrate_articles(sqlite_conn, pg_conn):
    print("\nMigrating articles...")

    total_sqlite = sqlite_conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    print(f"  Total articles in SQLite: {total_sqlite:,}")

    rows = sqlite_conn.execute("""
        SELECT title, description, text, source, source_id, bias,
               url, published_at, crawled_at, word_count, language,
               topic_hints, embedding, sentiment, emotion, emotion_scores
        FROM articles
        ORDER BY rowid
    """).fetchall()

    cur = pg_conn.cursor()
    migrated = 0
    skipped_embed = 0
    conflict = 0

    skipped_bad = 0

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        for row in batch:
            (title, description, text, source, source_id, bias,
             url, published_at, crawled_at, word_count, language,
             topic_hints, embedding_blob, sentiment, emotion, emotion_scores) = row

            if not url or not title or not source or not source_id:
                continue

            embedding_str = load_embedding(embedding_blob)
            if embedding_blob is not None and embedding_str is None:
                skipped_embed += 1

            try:
                wc = int(word_count) if word_count is not None else 0
            except (TypeError, ValueError):
                wc = 0

            try:
                cur.execute("""
                    INSERT INTO articles
                        (title, description, text, source, source_id, bias,
                         url, published_at, crawled_at, word_count, language,
                         topic_hints, embedding, sentiment, emotion, emotion_scores)
                    VALUES
                        (%s, %s, %s, %s, %s, %s,
                         %s, %s, %s, %s, %s,
                         %s, %s::vector, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                """, (
                    title, description, text, source, source_id, bias,
                    url, published_at, crawled_at,
                    wc, language or "de",
                    topic_hints or "[]",
                    embedding_str,
                    sentiment, emotion, emotion_scores,
                ))

                if cur.rowcount == 0:
                    conflict += 1
                else:
                    migrated += 1

            except Exception as e:
                pg_conn.rollback()
                skipped_bad += 1
                print(f"  [WARN] Skipped row (url={url!r}): {e}", flush=True)
                cur = pg_conn.cursor()

        pg_conn.commit()
        done = min(i + BATCH_SIZE, len(rows))
        print(f"  {done:,}/{len(rows):,} processed — {migrated:,} inserted, {conflict:,} skipped (url conflict), {skipped_bad} bad rows", flush=True)

    cur.close()
    print(f"\n  Articles migrated:      {migrated:,}")
    print(f"  URL conflicts skipped:  {conflict:,}")
    print(f"  Embeddings with errors: {skipped_embed:,} (stored as NULL)")
    print(f"  Bad rows skipped:       {skipped_bad:,}")
    return migrated


def migrate_crawl_log(sqlite_conn, pg_conn):
    print("\nMigrating crawl_log...")

    rows = sqlite_conn.execute(
        "SELECT crawled_at, source_id, articles_found, articles_new FROM crawl_log"
    ).fetchall()
    print(f"  Rows in SQLite crawl_log: {len(rows):,}")

    cur = pg_conn.cursor()
    migrated = 0
    for row in rows:
        crawled_at, source_id, articles_found, articles_new = row
        cur.execute("""
            INSERT INTO crawl_log (crawled_at, source_id, articles_found, articles_new)
            VALUES (%s, %s, %s, %s)
        """, (crawled_at, source_id, articles_found or 0, articles_new or 0))
        migrated += 1

    pg_conn.commit()
    cur.close()
    print(f"  crawl_log rows migrated: {migrated:,}")
    return migrated


def validate(sqlite_conn, pg_conn):
    print("\nValidation:")

    sq_articles = sqlite_conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    sq_embed = sqlite_conn.execute(
        "SELECT COUNT(*) FROM articles WHERE embedding IS NOT NULL"
    ).fetchone()[0]
    sq_crawl = sqlite_conn.execute("SELECT COUNT(*) FROM crawl_log").fetchone()[0]

    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM articles")
    pg_articles = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM articles WHERE embedding IS NOT NULL")
    pg_embed = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM crawl_log")
    pg_crawl = cur.fetchone()[0]
    cur.close()

    print(f"  {'':30} {'SQLite':>10} {'PostgreSQL':>12}")
    print(f"  {'articles (total)':30} {sq_articles:>10,} {pg_articles:>12,}")
    print(f"  {'articles (with embedding)':30} {sq_embed:>10,} {pg_embed:>12,}")
    print(f"  {'crawl_log rows':30} {sq_crawl:>10,} {pg_crawl:>12,}")

    if pg_articles == 0:
        print("\n  WARNING: No articles in PostgreSQL — something went wrong.")
    elif pg_articles < sq_articles * 0.95:
        print(f"\n  WARNING: PostgreSQL has significantly fewer articles than SQLite.")
    else:
        print(f"\n  Migration looks good.")


def run():
    print("Connecting to SQLite...")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)

    print("Connecting to Railway PostgreSQL...")
    pg_conn = psycopg2.connect(DATABASE_URL)

    if not check_embedding_format(sqlite_conn):
        sqlite_conn.close()
        pg_conn.close()
        sys.exit(1)

    migrate_articles(sqlite_conn, pg_conn)
    migrate_crawl_log(sqlite_conn, pg_conn)
    validate(sqlite_conn, pg_conn)

    sqlite_conn.close()
    pg_conn.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    run()
