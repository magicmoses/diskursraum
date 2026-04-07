"""
sentiment_analyzer.py — Sentiment & Emotion Analysis for German News Articles

Sentiment Model: oliverguhr/german-sentiment-bert
- Trained on 1.834 million German texts
- BERT architecture, F1 > 90% on German benchmarks
- Returns: positive / negative / neutral
- Stored in: articles.sentiment

Emotion Model: AnasAlokla/multilingual_go_emotions_V1.2
- Multilingual model (German/English/Arabic etc.)
- Multi-label: returns scores for all emotion categories
- Labels: joy, sadness, anger, fear, surprise, disgust,
          disappointment, approval, neutral and more
- Stored in: articles.emotion (dominant), articles.emotion_scores (all scores as JSON)

Architecture: Incremental cache in SQLite (same pattern as embeddings)
- Sentiment and emotions computed once per article, stored in DB
- Only new articles processed on each run
"""

import os
import sys
import sqlite3
from datetime import datetime
import json

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

def init_emotion_column(db_path: str = DB_PATH):
    """Adds emotion columns to articles table if not exists."""
    conn = sqlite3.connect(db_path)
    cols = [row[1] for row in conn.execute("PRAGMA table_info(articles)")]
    if "emotion" not in cols:
        conn.execute("ALTER TABLE articles ADD COLUMN emotion TEXT")
        conn.commit()
        print("✓ Added emotion column")
    if "emotion_scores" not in cols:
        conn.execute("ALTER TABLE articles ADD COLUMN emotion_scores TEXT")
        conn.commit()
        print("✓ Added emotion_scores column")
    conn.close()


def compute_and_cache_emotions(db_path: str = DB_PATH, batch_size: int = 32):
    """
    Computes emotions for articles that don't have them yet.
    Model: AnasAlokla/multilingual_go_emotions_V1.2
    - Multilingual (works on German)
    - Multi-label (returns scores for all emotions)
    - Labels: joy, sadness, anger, fear, surprise, disgust,
              disappointment, approval, neutral, etc.
    """
    init_emotion_column(db_path)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT id, text FROM articles
        WHERE emotion IS NULL
        AND word_count >= 10
    """).fetchall()

    if not rows:
        print("✓ All articles already have emotion scores")
        conn.close()
        return

    print(f"Computing emotions for {len(rows)} articles...")
    print("Loading multilingual_go_emotions model...")

    from transformers import pipeline
    emotion_classifier = pipeline(
        "text-classification",
        model="AnasAlokla/multilingual_go_emotions_V1.2",
        top_k=None,
        truncation=True,
        max_length=512
    )

    ids = [row[0] for row in rows]
    texts = [row[1][:512] for row in rows]

    for i in range(0, len(texts), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_texts = texts[i:i + batch_size]

        try:
            results = emotion_classifier(batch_texts)
        except Exception as e:
            print(f"  ⚠ Batch {i} failed: {e}")
            continue

        for article_id, result in zip(batch_ids, results):
            # result is list of {label, score}
            scores = {r["label"]: round(float(r["score"]), 4) for r in result}
            dominant = max(scores, key=scores.get)

            conn.execute(
                "UPDATE articles SET emotion = ?, emotion_scores = ? WHERE id = ?",
                (dominant, json.dumps(scores), article_id)
            )

        conn.commit()
        print(f"  Processed {min(i + batch_size, len(texts))}/{len(texts)}")

    conn.close()
    print(f"✓ Saved emotion scores for {len(rows)} articles")


if __name__ == "__main__":
    compute_and_cache_sentiment()
    compute_and_cache_emotions()