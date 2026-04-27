"""
bridging_scorer.py — Medienspiegel Analysis Pipeline

Inspired by Plurality (Audrey Tang, Glen Weyl) and Taiwan's Pol.is platform.
Goal: Transparency about media diversity in an increasingly polarized discourse.

Pipeline:
  1. Broad retrieval — keywords against title + text
  2. LLM relevance filter — "Is this article really about topic X?"
  3. Per-outlet aggregation — emotion, volume, sample titles
  4. LLM synthesis — shared perspectives + controversial points
  5. Cache results in DB for fast frontend delivery
"""

import os
import sys
import json
import re
import sqlite3
import pickle
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config import BIAS_SOURCES, SOURCE_BIAS, BIAS_SPECTRUM
from topics import TOPICS

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "news.db"
)

TOPIC_KEYWORDS = {
    "migration": [
        "migration", "migrationspolitik", "migranten", "migrant",
        "asyl", "asylpolitik", "asylbewerber", "asylrecht", "asylverfahren",
        "asylantrag", "asylsuchende", "asylunterkunft",
        "flüchtlinge", "flüchtlingspolitik", "flüchtlingskrise",
        "flüchtlingsunterkunft", "flüchtlingsheim",
        "einwanderung", "einwanderungsgesetz", "einwanderungsland",
        "abschiebung", "abschiebungen", "abschiebestopp", "abschiebehaft",
        "geflüchtete", "schutzsuchende", "schutzstatus",
        "grenzschutz", "grenzkontrollen", "grenzöffnung",
        "migrationsdebatte", "zuwanderung", "zuwanderer",
        "aufenthaltsrecht", "aufenthaltserlaubnis", "bleiberecht",
        "integration", "integrationspolitik", "integrationsgesetz",
        "illegale einwanderung", "irreguläre migration",
        "dublin abkommen", "seenotrettung",
        "syrien rückkehr", "afghanen", "afghanen abschiebung",
    ],
    "energy_transition": [
        "energiewende", "energie wende",
        "erneuerbare energien", "erneuerbare",
        "atomkraft", "atomausstieg", "atomenergie",
        "kernenergie", "kernkraft", "kernkraftwerk", "akw",
        "solarenergie", "solaranlage", "photovoltaik", "solarpanel",
        "windenergie", "windkraft", "windrad", "windräder", "windpark",
        "offshore wind", "onshore wind",
        "kohleausstieg", "kohleenergie", "braunkohle", "steinkohle",
        "klimaneutral", "co2 neutralität", "netto null", "treibhausgase",
        "energiepolitik", "klimapolitik", "klimaschutzgesetz",
        "strompreise", "energiekosten", "energieversorgung",
        "gasversorgung", "gaspreise", "flüssiggas", "lng",
        "wasserstoff", "grüner wasserstoff",
        "stromnetz", "netzausbau", "energiespeicher",
        "wärmepumpe", "heizungsgesetz", "gebäudeenergiegesetz",
        "klimapaket", "klimaziele",
    ],
    "retirement": [
        "rente", "rentenpolitik", "rentenreform", "rentenpaket",
        "rentenalter", "renteneintrittsalter",
        "rente mit 63", "rente mit 67", "rente mit 70",
        "rentenerhöhung", "rentenanpassung", "rentenniveau",
        "rentenlücke", "rentenkürzung", "rentenfinanzierung",
        "altersarmut", "altersvorsorge", "altersrente",
        "gesetzliche rentenversicherung", "rentenversicherung",
        "generationenvertrag", "demographischer wandel",
        "aktienrente", "kapitalgedeckte rente",
        "riester rente", "betriebliche altersvorsorge",
        "rentensystem", "rentenversprechen",
        "frühverrentung", "frühzeitig in rente",
        "grundrente", "mindestrente",
        "rentenkommission", "rentenberater",
    ],
    "wealth_tax": [
        "vermögenssteuer", "reichensteuer", "vermögensabgabe",
        "millionärssteuer", "milliardärssteuer", "milliardäre steuer",
        "superreiche", "ultrareiche", "hochvermögende",
        "vermögensungleichheit", "vermögensverteilung",
        "umverteilung", "umverteilungspolitik",
        "erbschaftssteuer", "erbschaftsteuer", "erbschaftssteuerreform",
        "schenkungssteuer",
        "steuergerechtigkeit", "steuerreform", "steuererhöhung",
        "spitzensteuersatz", "einkommensteuer erhöhung",
        "kapitalertragsteuer", "abgeltungssteuer",
        "finanztransaktionssteuer", "börsenumsatzsteuer",
        "steuerparadies", "steueroasen", "steuervermeidung",
        "vermögen ungleichheit", "reichtumsverteilung",
        "soziale ungleichheit", "schere arm reich",
    ],
    "digitalization": [
        "digitalisierung", "digitale transformation", "digitalstrategie",
        "künstliche intelligenz", "ki", "chatgpt", "llm", "sprachmodell",
        "maschinelles lernen", "deep learning", "neural network",
        "automatisierung", "robotisierung", "automatisiert",
        "digitale infrastruktur", "breitbandausbau", "glasfaser", "5g",
        "e-government", "digitale verwaltung", "onlinezugangsgesetz", "ozg",
        "industrie 4.0", "smart factory", "internet of things",
        "datenschutz", "dsgvo", "datensouveränität", "datensicherheit",
        "cybersicherheit", "cyberangriff", "cyberkriminalität", "hacker",
        "digitale bildung", "ki bildung", "coding", "programmieren",
        "eu ai act", "ki regulierung", "ki gesetz", "algorithmus",
        "plattformökonomie", "big tech", "digitalsteuer", "plattformsteuer",
        "arbeitsmarkt digitalisierung", "ki arbeitsplätze", "ki jobs",
        "social media", "desinformation", "fake news digital",
        "blockchain", "kryptowährung", "bitcoin",
        "cloud computing", "saas", "digitale souveränität",
        "quantencomputer", "chip industrie", "halbleiter",
    ],
}

TOPIC_DESCRIPTIONS = {
    "migration": (
        "Migration und Asylpolitik in Deutschland. Dieser Themenbereich umfasst die gesamte "
        "Debatte rund um Einwanderung, Asylrecht und Asylverfahren, Abschiebungen und "
        "Rückführungen, die Integration von Geflüchteten und Migranten, Grenzkontrollen, "
        "sowie politische Positionen von Parteien zur Migrationspolitik. Auch Artikel über "
        "konkrete Ereignisse wie Abschiebungen nach Syrien oder Afghanistan, Debatten über "
        "das Asylrecht oder Berichte über Flüchtlingsunterkünfte gehören dazu."
    ),
    "energy_transition": (
        "Die deutsche Energiewende und Klimapolitik. Dazu gehören Debatten über Atomkraft "
        "und Atomausstieg, den Ausbau erneuerbarer Energien wie Wind- und Solarenergie, "
        "den Kohleausstieg, Strompreise und Energieversorgungssicherheit, Klimaschutzziele "
        "und CO2-Neutralität, das Heizungsgesetz, Wasserstofftechnologie sowie die "
        "politische und gesellschaftliche Debatte über den richtigen Energiemix für Deutschland."
    ),
    "retirement": (
        "Das deutsche Rentensystem und die Debatte um Altersvorsorge. Dieser Themenbereich "
        "umfasst Rentenreformen und Rentenerhöhungen, das Renteneintrittsalter und Debatten "
        "über Rente mit 63, 67 oder 70, Altersarmut und Rentenlücken, die Aktienrente und "
        "kapitalgedeckte Vorsorge, den demographischen Wandel als Herausforderung für das "
        "Rentensystem, die Riester-Rente sowie grundsätzliche Fragen zur "
        "Generationengerechtigkeit und Finanzierbarkeit der gesetzlichen Rentenversicherung."
    ),
    "wealth_tax": (
        "Vermögenssteuer, Umverteilung und Steuergerechtigkeit in Deutschland. Dazu gehören "
        "Forderungen nach einer Vermögenssteuer oder Reichensteuer, Debatten über die "
        "Erbschaftssteuer und deren Reform, Diskussionen über den Spitzensteuersatz und "
        "Einkommensteuerpolitik, die Frage der Besteuerung von Superreichen und "
        "Milliardären, Steuervermeidung und Steueroasen, sowie grundsätzliche "
        "gesellschaftliche Debatten über Vermögensungleichheit und die Schere zwischen "
        "Arm und Reich in Deutschland."
    ),
    "digitalization": (
        "Digitalisierung, Künstliche Intelligenz und digitale Transformation in Deutschland "
        "und Europa. Dieser Themenbereich umfasst KI-Entwicklungen und Large Language Models, "
        "die Digitalisierung von Verwaltung und Wirtschaft, Datenschutz und Cybersicherheit, "
        "den Breitbandausbau und digitale Infrastruktur, den EU AI Act und KI-Regulierung, "
        "Automatisierung und deren Auswirkungen auf den Arbeitsmarkt, digitale Bildung, "
        "sowie die gesellschaftliche und politische Debatte über Chancen und Risiken "
        "von KI und Digitalisierung für Deutschland."
    ),
}

GROQ_MODEL = "llama-3.3-70b-versatile"
OLLAMA_MODEL = "llama3.1"


# ── Unified LLM Call ──────────────────────────────
def call_llm(prompt: str, max_tokens: int = 300) -> str:
    """
    Unified LLM call — uses Ollama or Groq based on LLM_PROVIDER env variable.
    Defaults to Groq if not set.
    """
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "ollama":
        import requests as req
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", OLLAMA_MODEL)
        response = req.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120
        )
        return response.json().get("response", "")
    else:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()


# ── DB Setup ──────────────────────────────────────
def init_db(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cols = [row[1] for row in conn.execute("PRAGMA table_info(articles)")]
    for col in ["sentiment", "emotion", "emotion_scores"]:
        if col not in cols:
            conn.execute(f"ALTER TABLE articles ADD COLUMN {col} TEXT")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            topic_id      TEXT PRIMARY KEY,
            computed_at   TEXT,
            article_count INTEGER,
            result_json   TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_result(topic_id: str, result: dict, db_path: str = DB_PATH):
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
    # Zusätzlich als JSON-Datei für Deployment
    results_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "results")
    os.makedirs(results_dir, exist_ok=True)
    with open(os.path.join(results_dir, f"{topic_id}.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    conn.commit()
    conn.close()


def load_cached_result(topic_id: str, db_path: str = DB_PATH):
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


# ── Step 1: Broad Retrieval ───────────────────────
def load_topic_articles(topic_id: str, db_path: str = DB_PATH) -> list[dict]:
    """Broad keyword retrieval — title AND text."""
    keywords = TOPIC_KEYWORDS.get(topic_id, [])
    if not keywords:
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conditions = " OR ".join([
        f"(LOWER(title) LIKE '%{kw}%' OR LOWER(text) LIKE '%{kw}%')"
        for kw in keywords
    ])

    rows = conn.execute(f"""
        SELECT id, title, text, source, source_id, bias,
               url, sentiment, emotion, embedding
        FROM articles
        WHERE ({conditions})
        AND word_count >= 10
        ORDER BY crawled_at DESC
        LIMIT 800
    """).fetchall()
    conn.close()

    articles = []
    for row in rows:
        article = dict(row)
        if article.get("embedding"):
            try:
                article["embedding"] = pickle.loads(article["embedding"])
            except Exception:
                article["embedding"] = None
        articles.append(article)

    return articles


# ── Step 2: LLM Relevance Filter ─────────────────
def llm_relevance_filter(
    articles: list[dict], topic_id: str, batch_size: int = 50
) -> list[dict]:
    """
    Filters articles by actual relevance to topic using LLM.
    Sends batches of titles — asks which are truly about the topic.
    Falls back to all articles if LLM fails.
    """
    topic_desc = TOPIC_DESCRIPTIONS.get(topic_id, topic_id)
    relevant = []
    total_batches = (len(articles) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(articles), batch_size):
        batch = articles[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1

        titles_list = "\n".join([
            f"{i+1}. {a['title']}"
            for i, a in enumerate(batch)
        ])

        prompt = f"""You are filtering German news articles by topic relevance.

Topic: {topic_desc}

Article titles (numbered):
{titles_list}

Which of these articles are relevant to the topic?
Include articles that are DIRECTLY about the topic OR closely related to it.
Return ONLY a JSON array of the relevant article numbers.
Example: [1, 3, 5, 7]
If none are relevant, return: []"""

        try:
            raw = call_llm(prompt, max_tokens=200)
            match = re.search(r'\[.*?\]', raw, re.DOTALL)
            if match:
                indices = json.loads(match.group())
                added = 0
                for idx in indices:
                    if isinstance(idx, int) and 1 <= idx <= len(batch):
                        relevant.append(batch[idx - 1])
                        added += 1
                print(f"  Batch {batch_num}/{total_batches}: {added}/{len(batch)} relevant", flush=True)
            else:
                print(f"  Batch {batch_num}/{total_batches}: no valid JSON — including all")
                relevant.extend(batch)
        except Exception as e:
            print(f"  ⚠ Batch {batch_num} failed: {e} — including all", flush=True)
            relevant.extend(batch)

    return relevant


# ── Step 3: Per-Outlet Aggregation ───────────────
def aggregate_by_outlet(articles: list[dict]) -> dict:
    """Aggregates relevant articles per media outlet."""
    outlets = {}

    for article in articles:
        source_id = article.get("source_id", "unknown")
        source = article.get("source", source_id)
        bias = article.get("bias", "unknown")

        if source_id not in outlets:
            outlets[source_id] = {
                "source_id": source_id,
                "source": source,
                "bias": bias,
                "article_count": 0,
                "emotions": {},
                "sample_titles": [],
                "urls": [],
            }

        outlets[source_id]["article_count"] += 1

        emotion = article.get("emotion")
        if emotion and emotion != "neutral":
            outlets[source_id]["emotions"][emotion] = \
                outlets[source_id]["emotions"].get(emotion, 0) + 1

        if len(outlets[source_id]["sample_titles"]) < 4:
            outlets[source_id]["sample_titles"].append(article["title"])
            if article.get("url"):
                outlets[source_id]["urls"].append(article["url"])

    for outlet in outlets.values():
        if outlet["emotions"]:
            outlet["dominant_emotion"] = max(
                outlet["emotions"], key=outlet["emotions"].get
            )
            outlet["top_emotions"] = sorted(
                [{"emotion": e, "count": c} for e, c in outlet["emotions"].items()],
                key=lambda x: x["count"], reverse=True
            )[:3]
        else:
            outlet["dominant_emotion"] = "neutral"
            outlet["top_emotions"] = []
        del outlet["emotions"]

    return dict(sorted(
        outlets.items(),
        key=lambda x: x[1]["article_count"],
        reverse=True
    ))


# ── Step 4: LLM Synthesis ─────────────────────────
def llm_synthesize(articles: list[dict], topic_id: str) -> dict:
    """
    Identifies shared perspectives and controversial points
    across different media outlets using LLM.
    """
    topic_desc = TOPIC_DESCRIPTIONS.get(topic_id, topic_id)

    bias_samples = {}
    for article in articles:
        bias = article.get("bias", "unknown")
        if bias not in bias_samples:
            bias_samples[bias] = []
        if len(bias_samples[bias]) < 3:
            bias_samples[bias].append(article["title"])

    if len(bias_samples) < 2:
        return {
            "shared_perspectives": "Zu wenig Quellen für eine Synthese.",
            "controversial_points": "Zu wenig Quellen für eine Synthese.",
        }

    samples_text = "\n".join([
        f"{bias.upper()}:\n" + "\n".join(f"  - {t}" for t in titles)
        for bias, titles in bias_samples.items()
    ])

    prompt = f"""You are analyzing German news coverage of: {topic_desc}

Here are article titles grouped by media bias:
{samples_text}

In German, provide:
1. SHARED: 1-2 sentences on what perspectives ALL groups seem to share
2. CONTROVERSIAL: 1-2 sentences on where the coverage diverges most

Format your response as JSON:
{{"shared": "...", "controversial": "..."}}

Be specific and insightful. Reference actual content from the titles."""

    try:
        raw = call_llm(prompt, max_tokens=400)
        raw = re.sub(r'```json|```', '', raw).strip()
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            return {
                "shared_perspectives": result.get("shared", ""),
                "controversial_points": result.get("controversial", ""),
            }
        else:
            print(f"  ⚠ Synthesis: no valid JSON in response")
    except Exception as e:
        print(f"  ⚠ Synthesis failed: {e}")
        import traceback
        traceback.print_exc()

    return {
        "shared_perspectives": "Synthese nicht verfügbar.",
        "controversial_points": "Synthese nicht verfügbar.",
    }


# ── Main Analysis ─────────────────────────────────
def analyze_topic(topic_id: str, db_path: str = DB_PATH) -> dict:
    """Full Medienspiegel analysis pipeline."""
    print(f"\n🔍 Analyzing: {topic_id}")
    init_db(db_path)
    candidates = load_topic_articles(topic_id, db_path)
    print(f"  → {len(candidates)} candidates retrieved")
    if len(candidates) < 3:
        return {
            "error": f"Not enough articles for '{topic_id}' (found {len(candidates)})",
            "topic_id": topic_id,
            "article_count": len(candidates)
        }
    print(f"  → Running LLM relevance filter...")
    relevant = llm_relevance_filter(candidates, topic_id)
    print(f"  → {len(relevant)} relevant articles after filtering")
    if len(relevant) < 3:
        print(f"  ⚠ Too few after filtering — using all candidates")
        relevant = candidates
    outlets = aggregate_by_outlet(relevant)
    print(f"  → {len(outlets)} outlets represented")
    print(f"  → Generating synthesis...")
    synthesis = llm_synthesize(relevant, topic_id)
    bias_dist = {}
    for article in relevant:
        bias = article.get("bias", "unknown")
        bias_dist[bias] = bias_dist.get(bias, 0) + 1
    result = {
        "topic_id": topic_id,
        "topic_label": TOPICS.get(topic_id, {}).get("label", topic_id),
        "article_count": len(relevant),
        "candidate_count": len(candidates),
        "outlets": outlets,
        "bias_distribution": bias_dist,
        "shared_perspectives": synthesis["shared_perspectives"],
        "controversial_points": synthesis["controversial_points"],
        "cached_at": datetime.utcnow().isoformat(),
    }
    print(f"  ✅ Done")
    return result


def compute_all_topics(db_path: str = DB_PATH):
    """Pre-computes and caches all topic analyses. Called by GitHub Actions."""
    init_db(db_path)
    print("\n🦞 ConsensusAgent — Medienspiegel Analysis")
    print(f"   Topics: {list(TOPICS.keys())}\n")
    print(f"   LLM Provider: {os.getenv('LLM_PROVIDER', 'groq').upper()}\n")

    success = 0
    failed = 0

    for topic_id in TOPICS.keys():
        try:
            result = analyze_topic(topic_id, db_path)
            if "error" not in result:
                save_result(topic_id, result, db_path)
                print(f"  ✅ {topic_id} cached", flush=True)
                success += 1
            else:
                print(f"  ⚠ {topic_id}: {result['error']}")
                failed += 1
        except Exception as e:
            print(f"  ❌ {topic_id} failed: {e}", flush=True)
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n✅ Complete: {success} succeeded, {failed} failed")


if __name__ == "__main__":
    topic_id = sys.argv[1] if len(sys.argv) > 1 else "--all"

    if topic_id == "--all":
        compute_all_topics()
    else:
        init_db()
        result = analyze_topic(topic_id)
        if "error" in result:
            print(f"\nError: {result['error']}")
        else:
            save_result(topic_id, result)
            print(f"\n=== Result ===")
            print(f"Articles: {result['article_count']} (from {result['candidate_count']} candidates)")
            print(f"Outlets: {list(result['outlets'].keys())}")
            print(f"\nShared: {result['shared_perspectives']}")
            print(f"\nControversial: {result['controversial_points']}")