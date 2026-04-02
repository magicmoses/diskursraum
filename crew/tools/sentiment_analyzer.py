"""
sentiment_analyzer.py — German Sentiment Analysis for News Articles

Model: oliverguhr/german-sentiment-bert
- Trained on 1.834 million German texts
- BERT architecture, F1 > 90% on German benchmarks
- Returns: positive / negative / neutral

Architecture: Incremental cache in SQLite (same pattern as embeddings)
- Sentiment computed once per article, stored in DB
- Only new articles processed on each run
"""

import os
import sys
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "news.db"
)


def init_sentiment_column(db_path: str = DB_PATH):
    """Adds sentiment column to articles table if not exists."""
    conn = sqlite3.connect(db_path)
    cols = [row[1] for row in conn.execute("PRAGMA table_info(articles)")]
    if "sentiment" not in cols:
        conn.execute("ALTER TABLE articles ADD COLUMN sentiment TEXT")
        conn.commit()
        print("✓ Added sentiment column to articles table")
    conn.close()


def compute_and_cache_sentiment(db_path: str = DB_PATH, batch_size: int = 128):
    """
    Computes sentiment for articles that don't have it yet.
    Incremental — only processes new articles each run.
    """
    init_sentiment_column(db_path)

    conn = sqlite3.connect(db_path)

    # Get articles without sentiment
    rows = conn.execute("""
        SELECT id, text FROM articles
        WHERE sentiment IS NULL
        AND word_count >= 10
    """).fetchall()

    if not rows:
        print("✓ All articles already have sentiment")
        conn.close()
        return

    print(f"Computing sentiment for {len(rows)} articles...")
    print("Loading german-sentiment-bert model...")

    from germansentiment import SentimentModel
    model = SentimentModel()

    ids = [row[0] for row in rows]
    texts = [row[1][:512] for row in rows]  # BERT max 512 chars

    # Process in batches
    all_sentiments = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_sentiments = model.predict_sentiment(batch)
        all_sentiments.extend(batch_sentiments)
        print(f"  Processed {min(i + batch_size, len(texts))}/{len(texts)}")

    # Save to DB
    for article_id, sentiment in zip(ids, all_sentiments):
        conn.execute(
            "UPDATE articles SET sentiment = ? WHERE id = ?",
            (sentiment, article_id)
        )
    conn.commit()
    conn.close()
    print(f"✓ Saved {len(rows)} sentiment scores to DB")


if __name__ == "__main__":
    compute_and_cache_sentiment()