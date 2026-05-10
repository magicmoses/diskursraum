"""
clusterer.py — Embedding Cache & Trending Topics

Embedding Model: jinaai/jina-embeddings-v2-base-de
- German/English bilingual, optimized for German news text
- Supports up to 8192 tokens
- Source: https://huggingface.co/jinaai/jina-embeddings-v2-base-de

Architecture: Incremental embedding cache in SQLite
- Embeddings computed once per article, stored in DB
- Only new articles need embedding on each run
"""

import os
import sys
import json
import sqlite3
import numpy as np
import pickle
import re
from sklearn.preprocessing import normalize
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "news.db"
)

MODEL_NAME = "jinaai/jina-embeddings-v2-base-de"


# ── DB Setup ──────────────────────────────────────
def init_embedding_cache(db_path: str = DB_PATH):
    """Adds embedding column to articles table if not exists."""
    conn = sqlite3.connect(db_path)
    cols = [row[1] for row in conn.execute("PRAGMA table_info(articles)")]
    if "embedding" not in cols:
        conn.execute("ALTER TABLE articles ADD COLUMN embedding BLOB")
        conn.commit()
        print("✓ Added embedding column to articles table")
    conn.close()


# ── Embedding Cache ───────────────────────────────
def get_articles_needing_embeddings(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT id, text FROM articles
        WHERE embedding IS NULL
        AND word_count >= 10
    """).fetchall()
    return [{"id": row[0], "text": row[1]} for row in rows]


def save_embeddings(conn: sqlite3.Connection, article_ids: list, embeddings: np.ndarray):
    for article_id, embedding in zip(article_ids, embeddings):
        blob = pickle.dumps(embedding)
        conn.execute(
            "UPDATE articles SET embedding = ? WHERE id = ?",
            (blob, article_id)
        )
    conn.commit()


# ── Embedding Computation ─────────────────────────
def compute_and_cache_embeddings(db_path: str = DB_PATH, batch_size: int = 64):
    """
    Computes embeddings for articles that don't have them yet.
    Incremental — only processes new articles each run.
    """
    conn = sqlite3.connect(db_path)
    articles = get_articles_needing_embeddings(conn)

    if not articles:
        print("✓ All articles already have embeddings")
        conn.close()
        return

    print(f"Computing embeddings for {len(articles)} new articles...")
    print(f"Model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)

    texts = [a["text"] for a in articles]
    ids = [a["id"] for a in articles]

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(
            batch,
            show_progress_bar=True,
            batch_size=32
        )
        all_embeddings.extend(batch_embeddings)
        print(f"  Processed {min(i + batch_size, len(texts))}/{len(texts)}", flush=True)

    embeddings_array = normalize(np.array(all_embeddings))
    save_embeddings(conn, ids, embeddings_array)
    conn.close()
    print(f"✓ Saved {len(articles)} new embeddings to DB")


# ── Curated Topic List ────────────────────────────
CURATED_TOPICS = [
    # ── Kernthemen ────────────────────────────────
    "Migration",
    "Grundeinkommen",
    "Atomkraft",
    "Wehrpflicht",
    "Rente",
    "Tempolimit",
    "Sterbehilfe",
    "Künstliche Intelligenz",
    "KI Regulierung",
    # ── Aktuelle News Topics ──────────────────────
    "Iran",
    "Trump",
    "Ukraine",
    "Israel",
    "NATO",
    "Merz",
    "AfD",
    "Russland",
    "Bundeshaushalt",
    "Energiepreise",
    "Klimaschutz",
    "Bundeswehr",
    "Inflation",
    "Gaza",
    "Wirtschaft",
]


def get_trending_topics(days_back: int = 7, top_n: int = 20, db_path: str = DB_PATH) -> list[dict]:
    """
    Returns trending topics based on curated list + TF-IDF discovered topics.
    1. Curated topics always included as base
    2. TF-IDF + LLM discovers additional emerging topics
    3. All topics scored by article count from DB
    4. Sorted by relevance, deduplicated
    """
    from dotenv import load_dotenv
    load_dotenv()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, title, text, source, bias, url, crawled_at
        FROM articles
        WHERE crawled_at >= datetime('now', ?)
        AND word_count >= 10
        ORDER BY crawled_at DESC
    """, (f'-{days_back} days',)).fetchall()
    conn.close()

    if len(rows) < 20:
        return []

    articles = [dict(row) for row in rows]
    texts = [a["title"] + " " + a["text"] for a in articles]

    print(f"  Extracting keyword candidates from {len(articles)} articles...")

    german_stopwords = [
        "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer",
        "einen", "einem", "eines", "ich", "du", "er", "sie", "es", "wir",
        "ihr", "ihre", "ihrem", "ihren", "ihrer", "ihres", "sein", "seine",
        "seinen", "seinem", "seiner", "seines", "mein", "dein", "unser",
        "ist", "sind", "war", "waren", "hat", "haben", "wird", "werden",
        "wurde", "wurden", "hatte", "hatten", "habe", "hast",
        "soll", "sollen", "kann", "können", "muss", "müssen", "darf",
        "dürfen", "will", "wollen", "mag", "mögen", "worden",
        "gibt", "gab", "geht", "ging", "kommt", "kam", "sagte", "sagt",
        "macht", "machte", "steht", "stand", "bleibt", "blieb",
        "und", "oder", "aber", "nicht", "auch", "sich", "mit", "von",
        "auf", "an", "in", "im", "bei", "nach", "aus", "für",
        "zu", "als", "wie", "dass", "so", "noch", "mehr", "nur", "schon",
        "jetzt", "über", "durch", "bis", "seit", "vor", "unter", "zwischen",
        "gegen", "ohne", "während", "wegen", "trotz", "statt", "außer",
        "dabei", "damit", "dazu", "davon", "daran", "beim", "etwa",
        "rund", "laut", "bzw", "sowie", "jedoch", "trotzdem", "zwar",
        "bereits", "immer", "wieder", "dann", "wenn", "weil", "obwohl",
        "doch", "mal", "nun", "eben", "eigentlich", "einfach", "natürlich",
        "wirklich", "dort", "hier", "zwei", "drei", "vier", "fünf",
        "alle", "alles", "allem", "jeder", "jede", "jedes", "kein",
        "keine", "keinen", "nichts", "erste", "ersten", "letzte", "letzten",
        "neue", "neuen", "weitere", "anderen", "eigene", "eigenen",
        "menschen", "mann", "frau", "land", "welt", "zeit", "jahr",
        "jahre", "jahren", "heute", "gestern", "morgen", "prozent",
        "euro", "uhr", "deutsche", "deutschland", "deutschen",
        "berlin", "münchen", "hamburg", "weiter", "zurück", "leben",
        "arbeit", "frage", "fragen", "problem", "grund", "stunde",
        "tag", "tage", "wochen", "monat", "seite", "bereich", "teil",
        "könnte", "hätte", "wäre", "sollte", "müsste",
        "the", "and", "for", "that", "this", "with", "from", "have",
        "been", "will", "are", "was", "were", "has", "had", "not",
        "says", "said", "after", "their", "they", "which", "about",
        "more", "also", "would", "could", "should", "than", "when",
    ]

    vectorizer = TfidfVectorizer(
        max_features=1000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.8,
        stop_words=german_stopwords
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        tfidf_candidates = []
    else:
        feature_names = vectorizer.get_feature_names_out()
        mean_scores = tfidf_matrix.mean(axis=0).A1
        top_indices = mean_scores.argsort()[-150:][::-1]

        tfidf_candidates = []
        curated_lower = [t.lower() for t in CURATED_TOPICS]
        for i in top_indices:
            kw = feature_names[i]
            score = float(mean_scores[i])
            if (len(kw) >= 4
                    and not any(c.isdigit() for c in kw)
                    and kw.lower() not in curated_lower):
                tfidf_candidates.append({
                    "keyword": kw,
                    "score": round(score / mean_scores[top_indices[0]], 3)
                })

        print(f"  → {len(tfidf_candidates)} new keyword candidates (excl. curated)")

    extra_topics = []
    if tfidf_candidates:
        print(f"  Sending to LLM for semantic filtering...")
        llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()

        candidate_text = "\n".join([
            f"{c['keyword']}: {c['score']}"
            for c in tfidf_candidates[:100]
        ])

        prompt = f"""From these keyword candidates extracted from German news articles,
select up to 5 additional real political or social topics NOT already in this list:
{', '.join(CURATED_TOPICS)}

Candidates:
{candidate_text}

Rules:
- Short names only (1-2 words)
- Real recognizable topics only
- No generic words, verbs, place names, sports, celebrities
- Return ONLY a JSON array of strings: ["Topic1", "Topic2"]
- Return empty array if no valid new topics found: []"""

        try:
            if llm_provider == "ollama":
                import requests as req
                response = req.post(
                    f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/generate",
                    json={
                        "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=60
                )
                raw = response.json().get("response", "[]")
            else:
                from groq import Groq
                client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=100
                )
                raw = response.choices[0].message.content.strip()

            raw = re.sub(r'```json|```', '', raw).strip()
            json_match = re.search(r'\[.*?\]', raw, re.DOTALL)
            if json_match:
                extra_topics = [
                    t for t in json.loads(json_match.group())
                    if isinstance(t, str)
                ]
            print(f"  → LLM found {len(extra_topics)} additional topics: {extra_topics}")

        except Exception as e:
            print(f"  ⚠ LLM step failed: {e}")

    all_topics = CURATED_TOPICS + extra_topics
    seen = set()
    unique_topics = []
    for t in all_topics:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique_topics.append(t)

    conn = sqlite3.connect(db_path)
    results = []

    for topic_name in unique_topics:
        keyword = topic_name.lower()
        rows = conn.execute("""
            SELECT id, title, source, bias
            FROM articles
            WHERE crawled_at >= datetime('now', ?)
            AND (LOWER(title) LIKE ? OR LOWER(text) LIKE ?)
            AND word_count >= 10
        """, (f'-{days_back} days', f'%{keyword}%', f'%{keyword}%')).fetchall()

        bias_counts = {}
        sources = set()
        sample_titles = []

        for row in rows:
            bias = row[3] or "unknown"
            bias_counts[bias] = bias_counts.get(bias, 0) + 1
            sources.add(row[2])
            if len(sample_titles) < 3:
                sample_titles.append(row[1])

        results.append({
            "topic": topic_name,
            "article_count": len(rows),
            "source_count": len(sources),
            "bias_distribution": bias_counts,
            "sample_titles": sample_titles,
            "days_back": days_back,
            "is_core": topic_name in CURATED_TOPICS[:10]
        })

    conn.close()
    results.sort(key=lambda x: x["article_count"], reverse=True)
    print(f"  ✅ {len(results)} topics scored")
    return results[:top_n]