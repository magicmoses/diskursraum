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

Architecture: Incremental cache in PostgreSQL
- Sentiment and emotions computed once per article, stored in DB
- Only new articles processed on each run
"""

import os
import json
import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("RAILWAY_DATABASE_URL") or os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL or RAILWAY_DATABASE_URL not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def compute_and_cache_sentiment(batch_size: int = 128):
    """
    Computes sentiment for articles that don't have it yet.
    Incremental — only processes new articles each run.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, text FROM articles
        WHERE sentiment IS NULL
        AND word_count >= 10
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("✓ All articles already have sentiment")
        return

    print(f"Computing sentiment for {len(rows)} articles...")
    print("Loading german-sentiment-bert model...")

    from germansentiment import SentimentModel
    model = SentimentModel()

    ids = [r["id"] for r in rows]
    texts = [r["text"][:512] for r in rows]

    all_sentiments = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        all_sentiments.extend(model.predict_sentiment(batch))
        print(f"  Processed {min(i + batch_size, len(texts))}/{len(texts)}")

    conn = get_conn()
    cur = conn.cursor()
    for article_id, sentiment in zip(ids, all_sentiments):
        cur.execute(
            "UPDATE articles SET sentiment = %s WHERE id = %s",
            (sentiment, article_id),
        )
    conn.commit()
    cur.close()
    conn.close()
    print(f"✓ Saved {len(rows)} sentiment scores to DB")


def compute_and_cache_emotions(batch_size: int = 32):
    """
    Computes emotions for articles that don't have them yet.
    Model: AnasAlokla/multilingual_go_emotions_V1.2
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, text FROM articles
        WHERE emotion IS NULL
        AND word_count >= 10
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("✓ All articles already have emotion scores")
        return

    print(f"Computing emotions for {len(rows)} articles...")
    print("Loading multilingual_go_emotions model...")

    from transformers import pipeline
    emotion_classifier = pipeline(
        "text-classification",
        model="AnasAlokla/multilingual_go_emotions_V1.2",
        top_k=None,
        truncation=True,
        max_length=512,
    )

    ids = [r["id"] for r in rows]
    texts = [r["text"][:512] for r in rows]

    conn = get_conn()
    cur = conn.cursor()

    for i in range(0, len(texts), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_texts = texts[i:i + batch_size]

        try:
            results = emotion_classifier(batch_texts)
        except Exception as e:
            print(f"  ⚠ Batch {i} failed: {e}")
            continue

        for article_id, result in zip(batch_ids, results):
            scores = {r["label"]: round(float(r["score"]), 4) for r in result}
            dominant = max(scores, key=scores.get)
            cur.execute(
                "UPDATE articles SET emotion = %s, emotion_scores = %s WHERE id = %s",
                (dominant, json.dumps(scores), article_id),
            )

        conn.commit()
        print(f"  Processed {min(i + batch_size, len(texts))}/{len(texts)}")

    cur.close()
    conn.close()
    print(f"✓ Saved emotion scores for {len(rows)} articles")


if __name__ == "__main__":
    compute_and_cache_sentiment()
    compute_and_cache_emotions()
