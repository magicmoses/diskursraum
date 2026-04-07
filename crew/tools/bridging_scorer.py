"""
bridging_scorer.py — Two-Level Bridging Score with Pre-computation Cache

Conceptually inspired by Taiwan's Pol.is bridging algorithm.
Applied to German news media using bias groups as opinion clusters.

Two-Level Bridging Score:
  Level 1 — Bias-Group Bridging (70%):
    How similar is this article to articles from OTHER bias groups?
    e.g. taz article similar to FAZ articles → high bias-bridging

  Level 2 — Source Bridging (30%):
    How similar is this article to articles from OTHER sources
    within the same bias group?
    e.g. taz article similar to how Spiegel covers the same topic

  Final Score = 0.7 * bias_bridging + 0.3 * source_bridging

Caching:
  Results pre-computed and stored in DB (analysis_results table).
  Frontend loads cached JSON → no waiting time.
  GitHub Actions re-computes daily after crawl.

Future Work (Option C):
  LLM-based frame extraction before clustering would produce
  argument-level clusters instead of media-bias clusters.
  See README for details.
"""

import os
import sys
import json
import sqlite3
import pickle
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config import BIAS_SOURCES, SOURCE_BIAS, BIAS_SPECTRUM
from topics import TOPICS

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "news.db"
)

# Topic keyword map for article retrieval
TOPIC_KEYWORDS = {
    "migration":        ["migration", "asyl", "flüchtlinge", "einwanderung", "migrant"],
    "basic_income":     ["grundeinkommen", "bge", "basic income", "bedingungsloses"],
    "nuclear_energy":   ["atomkraft", "kernenergie", "akw", "kernkraft"],
    "military_service": ["wehrpflicht", "bundeswehr", "wehrdienst"],
    "retirement_age":   ["rente", "renteneintritt", "rentenalter", "rentenreform"],
    "speed_limit":      ["tempolimit", "autobahn", "geschwindigkeit"],
    "euthanasia":       ["sterbehilfe", "euthanasie", "sterbebegleitung"],
    "wealth_tax":       ["vermögenssteuer", "reichensteuer", "vermögensabgabe"],
    "ai_jobs":          ["ki arbeitsplätze", "automatisierung", "ki ersetzt", "jobverlust"],
    "ai_regulation":    ["ki regulierung", "ai regulation", "eu ai act", "ki ethik"],
}


# ── DB Setup ──────────────────────────────────────
def init_results_table(db_path: str = DB_PATH):
    """Creates analysis_results table if not exists."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            topic_id     TEXT PRIMARY KEY,
            computed_at  TEXT,
            article_count INTEGER,
            result_json  TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_result(topic_id: str, result: dict, db_path: str = DB_PATH):
    """Saves analysis result to DB cache."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT OR REPLACE INTO analysis_results
        (topic_id, computed_at, article_count, result_json)
        VALUES (?, ?, ?, ?)
    """, (
        topic_id,
        datetime.utcnow().isoformat(),
        result.get("article_count", 0),
        json.dumps(result, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()


def load_cached_result(topic_id: str, db_path: str = DB_PATH) -> dict | None:
    """Loads cached analysis result from DB."""
    conn = sqlite3.connect(db_path)
    row = conn.execute("""
        SELECT result_json, computed_at FROM analysis_results
        WHERE topic_id = ?
    """, (topic_id,)).fetchone()
    conn.close()

    if row:
        result = json.loads(row[0])
        result["cached_at"] = row[1]
        return result
    return None


# ── Article Loading ───────────────────────────────
def load_topic_articles(topic_id: str, db_path: str = DB_PATH) -> list[dict]:
    keywords = TOPIC_KEYWORDS.get(topic_id, [topic_id.replace("_", " ")])

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Title match = starkes Signal, Text match = schwächeres Signal
    # Kombination: Titel ODER Text mit mindestens 2 verschiedenen Keywords
    title_conditions = " OR ".join([
        f"LOWER(title) LIKE '%{kw}%'" for kw in keywords
    ])
    text_conditions = " OR ".join([
        f"LOWER(text) LIKE '%{kw}%'" for kw in keywords
    ])

    rows = conn.execute(f"""
        SELECT id, title, text, source, source_id, bias,
               url, sentiment, emotion, embedding,
               -- Relevanz-Score: Titel-Match zählt 3x mehr als Text-Match
               CASE WHEN ({title_conditions}) THEN 3 ELSE 1 END as relevance
        FROM articles
        WHERE ({title_conditions} OR {text_conditions})
        AND embedding IS NOT NULL
        AND word_count >= 10
        -- Schließe Artikel aus die primär über andere Themen berichten
        AND NOT (
            LOWER(title) LIKE '%iran%' AND
            NOT ({title_conditions})
        )
        ORDER BY relevance DESC, crawled_at DESC
        LIMIT 500
    """).fetchall()
    conn.close()

    articles = []
    for row in rows:
        article = dict(row)
        if article["embedding"]:
            try:
                article["embedding"] = pickle.loads(article["embedding"])
            except Exception:
                continue
        articles.append(article)

    return articles


# ── Bridging Score ────────────────────────────────
def compute_two_level_bridging(articles: list[dict]) -> list[float]:
    """
    Computes two-level bridging score for each article.

    Level 1 (70%): Bias-group bridging
        Average cosine similarity to articles from OTHER bias groups

    Level 2 (30%): Source bridging
        Average cosine similarity to articles from OTHER sources
        within the same bias group
    """
    embeddings = np.array([a["embedding"] for a in articles])
    scores = []

    for i, article in enumerate(articles):
        emb = embeddings[i].reshape(1, -1)
        article_bias = article.get("bias", "unknown")
        article_source = article.get("source_id", "unknown")

        # ── Level 1: Bias-Group Bridging ──────────
        other_bias_sims = []
        for bias_group in BIAS_SPECTRUM:
            if bias_group == article_bias:
                continue
            # Find articles from this bias group
            other_indices = [
                j for j, a in enumerate(articles)
                if a.get("bias") == bias_group
            ]
            if not other_indices:
                continue
            other_embs = embeddings[other_indices]
            sims = cosine_similarity(emb, other_embs)[0]
            other_bias_sims.append(float(np.mean(sims)))

        bias_bridging = float(np.mean(other_bias_sims)) if other_bias_sims else 0.0

        # ── Level 2: Source Bridging ───────────────
        other_source_sims = []
        for j, other in enumerate(articles):
            if j == i:
                continue
            if other.get("bias") != article_bias:
                continue
            if other.get("source_id") == article_source:
                continue
            sim = cosine_similarity(emb, embeddings[j].reshape(1, -1))[0][0]
            other_source_sims.append(float(sim))

        source_bridging = float(np.mean(other_source_sims)) if other_source_sims else 0.0

        # ── Combined Score ─────────────────────────
        final_score = 0.7 * bias_bridging + 0.3 * source_bridging
        scores.append(round(final_score, 4))

    return scores


# ── Main Analysis ─────────────────────────────────
def analyze_topic(topic_id: str, db_path: str = DB_PATH) -> dict:
    """
    Full topic analysis:
    1. Load articles with embeddings
    2. Compute two-level bridging scores
    3. Build bias-group clusters
    4. Return structured result for caching
    """
    print(f"\n🔍 Analyzing: {topic_id}")

    articles = load_topic_articles(topic_id, db_path)
    print(f"  → {len(articles)} articles loaded")

    if len(articles) < 6:
        return {
            "error": f"Not enough articles for '{topic_id}' (found {len(articles)}, need 6+)",
            "topic_id": topic_id,
            "article_count": len(articles)
        }

    # Compute bridging scores
    print("  → Computing two-level bridging scores...")
    bridging_scores = compute_two_level_bridging(articles)

    # Build bias-group clusters
    clusters = {}
    for bias in BIAS_SPECTRUM:
        bias_articles = [
            a for a in articles if a.get("bias") == bias
        ]
        if not bias_articles:
            continue

        # Sub-clusters by source
        sources = {}
        for a in bias_articles:
            sid = a.get("source_id", "unknown")
            if sid not in sources:
                sources[sid] = []
            sources[sid].append({
                "title": a["title"],
                "source": a["source"],
                "url": a["url"],
                "emotion": a.get("emotion"),
                "sentiment": a.get("sentiment"),
            })

        clusters[bias] = {
            "bias": bias,
            "article_count": len(bias_articles),
            "sources": sources,
            "sample_titles": [a["title"] for a in bias_articles[:3]]
        }

    # Scored articles — strip embeddings for JSON
    scored_articles = []
    for i, article in enumerate(articles):
        scored_articles.append({
            "title": article["title"],
            "text": article["text"][:200],
            "source": article["source"],
            "source_id": article.get("source_id"),
            "bias": article.get("bias"),
            "url": article["url"],
            "emotion": article.get("emotion"),
            "sentiment": article.get("sentiment"),
            "bridging_score": bridging_scores[i],
        })

    # Top bridging statements
    top_bridging = sorted(
        scored_articles,
        key=lambda x: x["bridging_score"],
        reverse=True
    )[:10]

    result = {
        "topic_id": topic_id,
        "topic_label": TOPICS.get(topic_id, {}).get("label", topic_id),
        "article_count": len(articles),
        "bias_clusters": clusters,
        "top_bridging_statements": top_bridging,
        "all_articles": scored_articles,
    }

    print(f"  ✅ Done — top bridging: {top_bridging[0]['title'][:60]}")
    print(f"     Score: {top_bridging[0]['bridging_score']:.4f}")

    return result


def compute_all_topics(db_path: str = DB_PATH):
    """
    Pre-computes and caches analysis for all 10 topics.
    Called by GitHub Actions daily after crawl.
    """
    init_results_table(db_path)

    print("\n🦞 ConsensusAgent — Pre-computing all topic analyses")
    print(f"   Topics: {list(TOPICS.keys())}\n")

    success = 0
    failed = 0

    for topic_id in TOPICS.keys():
        try:
            result = analyze_topic(topic_id, db_path)
            if "error" not in result:
                save_result(topic_id, result, db_path)
                success += 1
                print(f"  ✅ {topic_id} cached")
            else:
                print(f"  ⚠ {topic_id}: {result['error']}")
                failed += 1
        except Exception as e:
            print(f"  ❌ {topic_id} failed: {e}")
            failed += 1

    print(f"\n✅ Complete: {success} succeeded, {failed} failed")


# ── Quick test ────────────────────────────────────
if __name__ == "__main__":
    topic_id = sys.argv[1] if len(sys.argv) > 1 else "nuclear_energy"

    if topic_id == "--all":
        compute_all_topics()
    else:
        init_results_table()
        result = analyze_topic(topic_id)

        if "error" in result:
            print(f"\nError: {result['error']}")
        else:
            save_result(topic_id, result)
            print(f"\n=== Top 5 Bridging Statements ===")
            for i, a in enumerate(result["top_bridging_statements"][:5]):
                print(f"\n{i+1}. [{a['source']} / {a['bias']}] Score: {a['bridging_score']:.4f}")
                print(f"   {a['title']}")