import sqlite3

DB_PATH = "../../data/news.db"

conn = sqlite3.connect(DB_PATH)

# ── Diagnose ──────────────────────────────────────
print("=== Column NULL Status ===")
cols = [row[1] for row in conn.execute("PRAGMA table_info(articles)")]
print(f"Columns: {cols}\n")
for col in cols:
    try:
        null_count = conn.execute(
            f"SELECT COUNT(*) FROM articles WHERE {col} IS NULL"
        ).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        print(f"  {col:<20} NULL: {null_count:>6} / {total}")
    except Exception as e:
        print(f"  {col:<20} ERROR: {e}")

print()

# ── Fix word_count ────────────────────────────────
rows = conn.execute("""
    SELECT id, text FROM articles
    WHERE word_count IS NULL OR word_count = 0
""").fetchall()

print(f"Fixing word_count for {len(rows)} articles...")
for article_id, text in rows:
    wc = len(text.split()) if text else 0
    conn.execute(
        "UPDATE articles SET word_count = ? WHERE id = ?",
        (wc, article_id)
    )
conn.commit()
print("✓ word_count fixed")

# ── Fix language ──────────────────────────────────
rows = conn.execute("""
    SELECT id, source_id FROM articles
    WHERE language IS NULL
""").fetchall()

print(f"\nFixing language for {len(rows)} articles...")
for article_id, source_id in rows:
    language = "en" if source_id == "dw" else "de"
    conn.execute(
        "UPDATE articles SET language = ? WHERE id = ?",
        (language, article_id)
    )
conn.commit()
print("✓ language fixed")

# ── Fix topic_hints ───────────────────────────────
rows = conn.execute("""
    SELECT id FROM articles
    WHERE topic_hints IS NULL
""").fetchall()

print(f"\nFixing topic_hints for {len(rows)} articles...")
for (article_id,) in rows:
    conn.execute(
        "UPDATE articles SET topic_hints = '[]' WHERE id = ?",
        (article_id,)
    )
conn.commit()
print("✓ topic_hints fixed")

conn.close()
print("\n✅ All fixes applied")