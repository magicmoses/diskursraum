"""
clusterer.py — Dynamic Topic Clustering from News Database

Uses sentence embeddings to cluster ALL articles in the DB without
predefined topics. Topics emerge organically from the data.

Embedding Model: jinaai/jina-embeddings-v2-base-de
- German/English bilingual, optimized for German news text
- Superior to generic multilingual models on German benchmarks
- Supports up to 8192 tokens, no language bias for mixed DE/EN input
- Source: https://huggingface.co/jinaai/jina-embeddings-v2-base-de

Architecture: Incremental embedding cache in SQLite
- Embeddings computed once per article, stored in DB
- Only new articles need embedding on each run
- Re-clustering triggered when enough new articles accumulated
"""

import os
import sys
import json
import sqlite3
import numpy as np
import pickle
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "news.db"
)

# jinaai/jina-embeddings-v2-base-de
# German/English bilingual — best choice for German news text
# trust_remote_code=True required by Jina
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

    # Cluster results table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cluster_results (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            computed_at  TEXT,
            n_articles   INTEGER,
            n_clusters   INTEGER,
            silhouette   REAL,
            results_json TEXT
        )
    """)
    conn.commit()
    conn.close()


# ── Embedding Cache ───────────────────────────────
def get_articles_needing_embeddings(conn: sqlite3.Connection) -> list[dict]:
    """Returns articles that don't have embeddings yet."""
    rows = conn.execute("""
        SELECT id, text FROM articles
        WHERE embedding IS NULL
        AND word_count >= 10
    """).fetchall()
    return [{"id": row[0], "text": row[1]} for row in rows]


def save_embeddings(conn: sqlite3.Connection, article_ids: list, embeddings: np.ndarray):
    """Saves embeddings to DB as binary blobs."""
    for article_id, embedding in zip(article_ids, embeddings):
        blob = pickle.dumps(embedding)
        conn.execute(
            "UPDATE articles SET embedding = ? WHERE id = ?",
            (blob, article_id)
        )
    conn.commit()


def load_all_embeddings(conn: sqlite3.Connection) -> tuple[list, np.ndarray]:
    """Loads all cached embeddings from DB."""
    rows = conn.execute("""
        SELECT id, text, source, bias, title, url, embedding
        FROM articles
        WHERE embedding IS NOT NULL
        AND word_count >= 10
    """).fetchall()

    article_ids = []
    articles_meta = []
    embeddings = []

    for row in rows:
        article_ids.append(row[0])
        articles_meta.append({
            "id": row[0],
            "text": row[1],
            "source": row[2],
            "bias": row[3],
            "title": row[4],
            "url": row[5]
        })
        embeddings.append(pickle.loads(row[6]))

    return articles_meta, np.array(embeddings)


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

    # Process in batches
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(
            batch,
            show_progress_bar=True,
            batch_size=32
        )
        all_embeddings.extend(batch_embeddings)
        print(f"  Processed {min(i + batch_size, len(texts))}/{len(texts)}")

    embeddings_array = normalize(np.array(all_embeddings))
    save_embeddings(conn, ids, embeddings_array)
    conn.close()
    print(f"✓ Saved {len(articles)} new embeddings to DB")


# ── Clustering ────────────────────────────────────
def find_optimal_k(embeddings: np.ndarray, min_k: int = 5, max_k: int = 15) -> tuple[int, float]:
    """
    Finds optimal cluster count using silhouette score.
    Range 5-15 for a news dataset with diverse topics.
    """
    best_k = min_k
    best_score = -1

    for k in range(min_k, min(max_k + 1, len(embeddings) // 10)):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels, sample_size=min(1000, len(embeddings)))
        print(f"  k={k}: silhouette={score:.3f}")
        if score > best_score:
            best_score = score
            best_k = k

    return best_k, best_score


def extract_topic_label(texts: list[str]) -> str:
    """
    Extracts a topic label from a cluster using TF-IDF.
    Returns top 2 keywords as the topic name.
    """
    if not texts:
        return "Unknown"

    try:
        vectorizer = TfidfVectorizer(
            max_features=20,
            stop_words=None,  # German stopwords not built-in
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        mean_tfidf = tfidf_matrix.mean(axis=0).A1
        top_indices = mean_tfidf.argsort()[-3:][::-1]
        top_keywords = [feature_names[i] for i in top_indices]

        # Filter short words and numbers
        top_keywords = [
            kw for kw in top_keywords
            if len(kw) > 3 and not kw.isdigit()
        ]

        return " · ".join(top_keywords[:2]) if top_keywords else "Diverses"
    except Exception:
        return "Diverses"


def run_clustering(db_path: str = DB_PATH, force: bool = False) -> dict:
    """
    Main clustering function.
    1. Computes missing embeddings (incremental)
    2. Loads all embeddings
    3. Finds optimal cluster count
    4. Clusters and extracts topic labels
    5. Saves results to DB
    """
    init_embedding_cache(db_path)

    # Step 1: Compute missing embeddings
    compute_and_cache_embeddings(db_path)

    # Step 2: Load all embeddings
    print("\nLoading embeddings from DB...")
    conn = sqlite3.connect(db_path)
    articles_meta, embeddings = load_all_embeddings(conn)

    if len(articles_meta) < 50:
        conn.close()
        return {"error": f"Not enough articles with embeddings ({len(articles_meta)})"}

    print(f"✓ Loaded {len(articles_meta)} articles with embeddings")

    # Step 3: Find optimal k
    print("\nFinding optimal cluster count...")
    k, silhouette = find_optimal_k(embeddings)
    print(f"✓ Optimal k={k} (silhouette={silhouette:.3f})")

    # Step 4: Final clustering
    print(f"\nClustering {len(articles_meta)} articles into {k} clusters...")
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    # Step 5: Build cluster results
    clusters = []
    for cluster_id in range(k):
        cluster_indices = np.where(labels == cluster_id)[0]
        cluster_articles = [articles_meta[i] for i in cluster_indices]

        texts = [a["text"] for a in cluster_articles]
        topic_label = extract_topic_label(texts)

        # Bias distribution
        bias_counts = {}
        for a in cluster_articles:
            bias = a.get("bias", "unknown")
            bias_counts[bias] = bias_counts.get(bias, 0) + 1

        dominant_bias = max(bias_counts, key=bias_counts.get)

        # Sample articles
        samples = cluster_articles[:5]

        clusters.append({
            "cluster_id": cluster_id,
            "topic_label": topic_label,
            "size": len(cluster_articles),
            "dominant_bias": dominant_bias,
            "bias_distribution": bias_counts,
            "sample_articles": [
                {
                    "title": a["title"],
                    "source": a["source"],
                    "bias": a["bias"],
                    "url": a["url"]
                }
                for a in samples
            ]
        })

    # Sort by size
    clusters.sort(key=lambda x: x["size"], reverse=True)

    result = {
        "computed_at": datetime.utcnow().isoformat(),
        "total_articles": len(articles_meta),
        "n_clusters": k,
        "silhouette_score": round(silhouette, 3),
        "clusters": clusters
    }

    # Save to DB
    conn.execute("""
        INSERT INTO cluster_results
        (computed_at, n_articles, n_clusters, silhouette, results_json)
        VALUES (?, ?, ?, ?, ?)
    """, (
        result["computed_at"],
        result["total_articles"],
        result["n_clusters"],
        result["silhouette_score"],
        json.dumps(clusters, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()

    print(f"\n✅ Clustering complete")
    print(f"   Articles:   {result['total_articles']}")
    print(f"   Clusters:   {result['n_clusters']}")
    print(f"   Silhouette: {result['silhouette_score']}")
    print()
    for c in clusters[:5]:
        print(f"   Cluster {c['cluster_id']:2d} [{c['size']:4d} articles] — {c['topic_label']} ({c['dominant_bias']})")

    return result

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
    "Vermögenssteuer",
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

    1. Curated topics (Kernthemen + News) always included as base
    2. TF-IDF + LLM discovers additional emerging topics
    3. All topics scored by article count from DB
    4. Sorted by relevance, deduplicated
    """
    import os
    import re
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

    # ── Step 1: TF-IDF Keyword Extraction ─────────
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

    # ── Step 2: LLM filters TF-IDF candidates ─────
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

    # ── Step 3: Score all topics from DB ──────────
    all_topics = CURATED_TOPICS + extra_topics
    # Deduplicate case-insensitive
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

# ── Quick test ────────────────────────────────────
if __name__ == "__main__":
    result = run_clustering()
    if "error" in result:
        print(f"Error: {result['error']}")