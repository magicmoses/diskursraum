import os
import sys
import json
import sqlite3
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from topics import TOPICS

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "news.db"
)

# ── Model ─────────────────────────────────────────
# Multilingual model — handles German text well
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def load_articles(topic_id: str, min_words: int = 10, limit: int = 500) -> list[dict]:
    """
    Loads articles for a topic from SQLite.
    Uses topic_hints if available, otherwise falls back
    to keyword search across all articles.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # First try topic_hints
    rows = conn.execute("""
        SELECT id, title, text, source, bias, url, published_at
        FROM articles
        WHERE topic_hints LIKE ?
        AND word_count >= ?
        ORDER BY crawled_at DESC
        LIMIT ?
    """, (f'%"{topic_id}"%', min_words, limit)).fetchall()

    # Fallback: keyword search
    if len(rows) < 20:
        topic = TOPICS.get(topic_id, {})
        keywords = topic.get("newsapi_keywords", [])
        if keywords:
            keyword_filter = " OR ".join([f"text LIKE '%{kw}%'" for kw in keywords[:5]])
            rows = conn.execute(f"""
                SELECT id, title, text, source, bias, url, published_at
                FROM articles
                WHERE ({keyword_filter})
                AND word_count >= ?
                ORDER BY crawled_at DESC
                LIMIT ?
            """, (min_words, limit)).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def compute_embeddings(texts: list[str], model: SentenceTransformer) -> np.ndarray:
    """Computes normalized sentence embeddings."""
    embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)
    return normalize(embeddings)


def find_optimal_clusters(embeddings: np.ndarray, min_k: int = 3, max_k: int = 7) -> int:
    """
    Finds optimal cluster count using silhouette score.
    Agent decision: chooses k that maximizes cluster quality.
    """
    best_k = min_k
    best_score = -1

    for k in range(min_k, min(max_k + 1, len(embeddings))):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels)
        if score > best_score:
            best_score = score
            best_k = k

    return best_k, best_score


def cluster_articles(topic_id: str) -> dict:
    """
    Main clustering function.
    Returns structured result with clusters and metadata.
    """
    print(f"\n🔍 Clustering: {topic_id}")

    # 1. Load articles
    articles = load_articles(topic_id)
    print(f"  → {len(articles)} articles loaded")

    if len(articles) < 10:
        return {"error": f"Not enough articles for topic '{topic_id}' (found {len(articles)}, need 10+)"}

    # 2. Compute embeddings
    print("  → Computing embeddings...")
    model = SentenceTransformer(MODEL_NAME)
    texts = [a["text"] for a in articles]
    embeddings = compute_embeddings(texts, model)

    # 3. Find optimal cluster count
    print("  → Finding optimal cluster count...")
    k, silhouette = find_optimal_clusters(embeddings)
    print(f"  → Optimal k={k} (silhouette={silhouette:.3f})")

    # 4. Final clustering
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    # 5. Build cluster results
    clusters = []
    for cluster_id in range(k):
        cluster_indices = np.where(labels == cluster_id)[0]
        cluster_articles = [articles[i] for i in cluster_indices]

        # Bias distribution in this cluster
        bias_counts = {}
        for a in cluster_articles:
            bias = a.get("bias", "unknown")
            bias_counts[bias] = bias_counts.get(bias, 0) + 1

        # Dominant bias
        dominant_bias = max(bias_counts, key=bias_counts.get)

        # Sample articles (top 5 by position)
        samples = cluster_articles[:5]

        clusters.append({
            "cluster_id": cluster_id,
            "size": len(cluster_articles),
            "dominant_bias": dominant_bias,
            "bias_distribution": bias_counts,
            "sample_articles": [
                {
                    "title": a["title"],
                    "source": a["source"],
                    "bias": a["bias"],
                    "url": a["url"],
                }
                for a in samples
            ]
        })

    result = {
        "topic_id": topic_id,
        "topic_label": TOPICS.get(topic_id, {}).get("label", topic_id),
        "total_articles": len(articles),
        "n_clusters": k,
        "silhouette_score": round(silhouette, 3),
        "clusters": clusters,
        # Raw data for bridging analysis
        "_articles": articles,
        "_labels": labels.tolist(),
        "_embeddings": embeddings.tolist()
    }

    print(f"  ✅ Done — {k} clusters found")
    return result


# ── Quick test ────────────────────────────────────
if __name__ == "__main__":
    topic_id = sys.argv[1] if len(sys.argv) > 1 else "nuclear_energy"
    result = cluster_articles(topic_id)

    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\n=== Results ===")
        print(f"Topic:     {result['topic_label']}")
        print(f"Articles:  {result['total_articles']}")
        print(f"Clusters:  {result['n_clusters']}")
        print(f"Silhouette: {result['silhouette_score']}")
        print()
        for c in result["clusters"]:
            print(f"Cluster {c['cluster_id']} — {c['size']} articles — dominant: {c['dominant_bias']}")
            for a in c["sample_articles"][:2]:
                print(f"  [{a['source']}] {a['title'][:80]}")