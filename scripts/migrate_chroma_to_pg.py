"""
migrate_chroma_to_pg.py — One-time migration: ChromaDB manifesto chunks → pgvector

Seeds the manifesto_chunks table in Railway PostgreSQL from the local data/chroma_db/.
After this runs, the production API (frag_nach.py) has live vector search data.

Usage:
  python scripts/migrate_chroma_to_pg.py           # skip if table already populated
  python scripts/migrate_chroma_to_pg.py --force   # truncate + re-seed

Requirements:
  - data/chroma_db/ must exist locally (gitignored — built by pdf_processor.py)
  - RAILWAY_DATABASE_URL set in .env or environment
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
AVAILABLE_YEARS = [2005, 2009, 2013, 2017, 2021, 2025]
DATABASE_URL = os.getenv("RAILWAY_DATABASE_URL") or os.getenv("DATABASE_URL")


def _get_conn():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


def _setup_table(conn) -> None:
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS manifesto_chunks (
            id         SERIAL PRIMARY KEY,
            year       SMALLINT NOT NULL,
            party_id   TEXT NOT NULL,
            party_name TEXT NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding  vector(768) NOT NULL
        );
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS manifesto_chunks_embedding_idx
        ON manifesto_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS manifesto_chunks_year_party_idx
        ON manifesto_chunks (year, party_id);
    """)
    conn.commit()
    cur.close()


def migrate(force: bool = False) -> None:
    if not CHROMA_DIR.exists():
        print(f"[error] {CHROMA_DIR} not found. Run pdf_processor.py first to build local ChromaDB.")
        sys.exit(1)

    if not DATABASE_URL:
        print("[error] RAILWAY_DATABASE_URL / DATABASE_URL not set. Check your .env.")
        sys.exit(1)

    import chromadb

    print(f"[connect] Opening ChromaDB at {CHROMA_DIR}")
    chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))

    print(f"[connect] Connecting to PostgreSQL...")
    conn = _get_conn()
    _setup_table(conn)

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM manifesto_chunks")
    existing = cur.fetchone()[0]
    cur.close()

    if existing > 0 and not force:
        print(f"[skip] manifesto_chunks already has {existing:,} rows. Use --force to re-seed.")
        conn.close()
        return

    if force and existing > 0:
        print(f"[force] Truncating {existing:,} existing rows...")
        cur = conn.cursor()
        cur.execute("TRUNCATE manifesto_chunks RESTART IDENTITY;")
        conn.commit()
        cur.close()

    total = 0
    for year in AVAILABLE_YEARS:
        try:
            col = chroma.get_collection(f"manifestos_{year}")
        except Exception as e:
            print(f"[skip] manifestos_{year}: collection not found ({e})")
            continue

        result = col.get(include=["documents", "metadatas", "embeddings"])
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []
        embeddings_raw = result.get("embeddings")
        embeddings = embeddings_raw if embeddings_raw is not None else []

        if not docs:
            print(f"[skip] manifestos_{year}: empty collection")
            continue

        rows = []
        for doc, meta, emb in zip(docs, metas, embeddings):
            pid = meta.get("party_id", "")
            pname = meta.get("party_name", pid)
            vec_str = "[" + ",".join(map(str, emb)) + "]"
            rows.append((year, pid, pname, doc, vec_str))

        cur = conn.cursor()
        cur.executemany(
            "INSERT INTO manifesto_chunks (year, party_id, party_name, chunk_text, embedding) "
            "VALUES (%s, %s, %s, %s, %s::vector)",
            rows,
        )
        conn.commit()
        cur.close()

        print(f"[ok] manifestos_{year}: {len(docs):,} chunks → pgvector")
        total += len(docs)

    conn.close()
    print(f"\n[done] {total:,} chunks migrated. frag-nach is ready for production.")


if __name__ == "__main__":
    migrate(force="--force" in sys.argv)
