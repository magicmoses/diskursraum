"""
trending_analyzer.py — Trending Topics Analyse

Kombiniert drei Quellen:
1. Eigene DB: Keyword-Frequenz der letzten 7 Tage
2. Google Trends: Validierung via pytrends (kein API Key nötig)
3. LLM: Clustering und Benennung der Trends

Output: trending_topics.json mit zwei Listen:
- "deutschland": Themen mit direktem Deutschlandbezug
- "international": alle Themen inkl. internationale Ereignisse
"""

import os
import re
import json
import sqlite3
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DB_PATH = os.path.join(ROOT, "data", "news.db")
OUTPUT_PATH = os.path.join(ROOT, "data", "results", "analytics", "trending_topics.json")

GROQ_MODEL = "llama-3.3-70b-versatile"

GERMAN_STOPWORDS = [
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
    "warum", "viele", "vielen", "welche", "welcher", "welches",
    "diese", "diesen", "diesem", "dieses", "dieser",
    "jetzt", "gerade", "aktuell", "derzeit", "wann", "wohin",
    "etwas", "einige", "wenige", "weniger", "mehrere",
    "the", "and", "for", "that", "this", "with", "from", "have",
    "been", "will", "are", "was", "were", "has", "had", "not",
    "says", "said", "after", "their", "they", "which", "about",
    "more", "also", "would", "could", "should", "than", "when",
]


# ── LLM Call ──────────────────────────────────────
def _call_llm(prompt: str, max_tokens: int = 900) -> str:
    from dotenv import load_dotenv
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "ollama":
        import requests
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3.1")
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        return response.json().get("response", "")
    else:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()


# ── Step A: DB Frequency Analysis ─────────────────
def _extract_db_keywords(days_back: int = 7) -> list[dict]:
    """Extract top-50 keyword candidates from recent articles using TF-IDF."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT title, text FROM articles
        WHERE crawled_at >= datetime('now', ?)
        AND word_count >= 10
        ORDER BY crawled_at DESC
    """, (f"-{days_back} days",)).fetchall()
    conn.close()

    if len(rows) < 20:
        return []

    texts = [f"{r['title']} {r['text']}" for r in rows]

    vectorizer = TfidfVectorizer(
        max_features=1000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.8,
        stop_words=GERMAN_STOPWORDS,
    )

    try:
        tfidf = vectorizer.fit_transform(texts)
    except ValueError:
        return []

    feature_names = vectorizer.get_feature_names_out()
    mean_scores = tfidf.mean(axis=0).A1
    top_indices = mean_scores.argsort()[-50:][::-1]
    max_score = float(mean_scores[top_indices[0]]) if len(top_indices) > 0 else 1.0

    keywords = []
    for i in top_indices:
        kw = feature_names[i]
        if len(kw) >= 4 and not any(c.isdigit() for c in kw):
            keywords.append({
                "keyword": kw,
                "db_score": round(float(mean_scores[i]) / max_score, 3),
            })

    return keywords


# ── Step B: Google Trends Validation ──────────────
def _validate_with_trends(keywords: list[dict]) -> list[dict]:
    """Validate DB keywords against Google Trends. Degrades gracefully on failure."""
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="de-DE", tz=60, timeout=(10, 25), retries=1)
        batch = [k["keyword"] for k in keywords[:5]]

        pytrends.build_payload(batch, timeframe="now 7-d", geo="DE")
        trends_data = pytrends.interest_over_time()

        if not trends_data.empty:
            trends_scores = {}
            for kw in batch:
                if kw in trends_data.columns:
                    trends_scores[kw] = float(trends_data[kw].mean())

            if trends_scores:
                max_trend = max(trends_scores.values()) or 1.0
                for kw_dict in keywords:
                    kw = kw_dict["keyword"]
                    trend_norm = trends_scores.get(kw, 0) / max_trend
                    kw_dict["combined_score"] = round(
                        0.6 * kw_dict["db_score"] + 0.4 * trend_norm, 3
                    )
                keywords.sort(
                    key=lambda x: x.get("combined_score", x["db_score"]), reverse=True
                )
                print(f"  Google Trends: {len(trends_scores)} Keywords validiert")

    except Exception as e:
        print(f"  Google Trends nicht verfügbar: {e}")

    for kw in keywords:
        if "combined_score" not in kw:
            kw["combined_score"] = kw["db_score"]

    return keywords


# ── Step C: LLM Clustering ─────────────────────────
def _cluster_with_llm(keywords: list[dict]) -> list[dict]:
    """Cluster top-30 keywords into journalistic themes using LLM."""
    top30 = keywords[:30]
    kw_text = "\n".join(
        f"{k['keyword']}: {k['combined_score']:.3f}" for k in top30
    )

    prompt = f"""Du bist ein politischer Redakteur der deutschen Nachrichtenlandschaft.
Du bekommst eine Liste von Keywords mit Häufigkeitswerten aus deutschen Nachrichtenartikeln der letzten 7 Tage.

Keywords:
{kw_text}

Deine Aufgabe:
1. Fasse zusammengehörige Keywords zu maximal 8 Themen zusammen. Beispiel: Trump + USA + Zölle + Amerika = ein Thema "US-Handelspolitik"
2. Benenne jedes Thema präzise und journalistisch in 2-4 Wörtern auf Deutsch.
3. Trenne strikt: was betrifft Deutschland direkt vs. was ist international.
4. Gib für jedes Thema an: hat direkten Deutschlandbezug (true/false)

Antworte NUR als JSON:
{{
  "themen": [
    {{
      "name": "Themenname",
      "keywords": ["keyword1", "keyword2"],
      "relevanz": 0.85,
      "deutschland_bezug": true
    }}
  ]
}}"""

    try:
        raw = _call_llm(prompt, max_tokens=900)
        raw = re.sub(r"```json|```", "", raw).strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            themen = result.get("themen", [])
            if themen:
                return themen
    except Exception as e:
        print(f"  LLM-Clustering fehlgeschlagen: {e}")

    return [
        {
            "name": k["keyword"].title(),
            "keywords": [k["keyword"]],
            "relevanz": k["combined_score"],
            "deutschland_bezug": True,
        }
        for k in keywords[:8]
    ]


# ── Main Entry Point ──────────────────────────────
def generate_trending_topics(days_back: int = 7) -> dict:
    """
    Full pipeline: DB frequency → Google Trends → LLM clustering.
    Returns dict with 'deutschland' and 'international' topic lists.
    """
    print("  Extracting keywords from DB...")
    keywords = _extract_db_keywords(days_back)

    if not keywords:
        print("  Nicht genug Artikel in DB")
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "deutschland": [],
            "international": [],
        }

    print(f"  {len(keywords)} Keywords extrahiert")

    print("  Google Trends Validierung...")
    keywords = _validate_with_trends(keywords)

    print("  LLM-Clustering...")
    themen = _cluster_with_llm(keywords)

    deutschland = []
    international = []

    for t in themen:
        entry = {
            "topic": t["name"],
            "relevanz": round(float(t.get("relevanz", 0.5)), 3),
            "keywords": t.get("keywords", []),
        }
        if t.get("deutschland_bezug"):
            deutschland.append(entry)
        else:
            international.append(entry)

    deutschland.sort(key=lambda x: x["relevanz"], reverse=True)
    international.sort(key=lambda x: x["relevanz"], reverse=True)

    result = {
        "generated_at": datetime.utcnow().isoformat(),
        "deutschland": deutschland,
        "international": international,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  Gespeichert: {OUTPUT_PATH}")

    return result


if __name__ == "__main__":
    result = generate_trending_topics()
    print(f"\ndeutschland: {len(result['deutschland'])} Themen")
    for t in result["deutschland"]:
        print(f"  [DE]   {t['topic']} ({t['relevanz']:.2f})")
    print(f"\ninternational: {len(result['international'])} Themen")
    for t in result["international"]:
        print(f"  [INTL] {t['topic']} ({t['relevanz']:.2f})")
