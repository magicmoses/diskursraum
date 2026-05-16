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
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from config import BIAS_SOURCES, SOURCE_BIAS, BIAS_SPECTRUM
from topics import TOPICS

DATABASE_URL = os.getenv("RAILWAY_DATABASE_URL") or os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL or RAILWAY_DATABASE_URL not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

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
    "work_transition": [
        "mindestlohn", "tarifbindung", "leiharbeit", "gewerkschaft", "arbeitszeit",
        "fachkräfte", "beschäftigung", "kurzarbeit", "werkverträge", "soziale sicherung",
        "arbeitslosigkeit", "grundsicherung", "bürgergeld", "hartz", "arbeitsmarkt",
        "vollbeschäftigung", "lohngleichheit", "equal pay", "betriebsrat",
        "mitbestimmung", "scheinselbstständigkeit", "plattformarbeit", "homeoffice",
        "automatisierung", "jobverlust", "qualifizierung", "umschulung", "fachkräftemangel",
        "kurzarbeitergeld", "arbeitnehmer", "arbeitgeber", "tarifvertrag", "streik",
    ],
    "defense": [
        "bundeswehr", "verteidigung", "nato", "rüstung", "wehrpflicht",
        "sicherheitspolitik", "auslandseinsätze", "rüstungsexporte", "zeitenwende",
        "bündnisverteidigung", "militär", "streitkräfte", "sicherheitsarchitektur",
        "landesverteidigung", "zivilschutz", "abrüstung", "friedenspolitik",
        "verteidigungshaushalt", "2-prozent-ziel", "waffenlieferungen",
        "kriegswaffenkontrolle", "bundeswehrreform", "reservisten", "sanitätsdienst",
        "cyberabwehr", "nato-beitritt", "bündnisfall", "artikel 5", "sicherheitsrat",
        "ukraine-hilfe", "panzer", "munition", "drohnen", "rüstungsindustrie",
    ],
    "family_children": [
        "familie", "kindergeld", "kita", "elterngeld", "kinderbetreuung",
        "familienleistungen", "erziehung", "alleinerziehende", "betreuungsgeld",
        "kinderfreibetrag", "familienpolitik", "vereinbarkeit", "kinderrechte",
        "kinderarmut", "jugendschutz", "jugendhilfe", "kinderschutz", "pflegekinder",
        "adoption", "elternzeit", "väter", "mütter", "geburtshilfe", "hebammen",
        "kinderzuschlag", "grundsicherung kinder", "chancengleichheit", "kindeswohl",
        "krippenplatz", "tagesmutter", "erzieher", "vorschule", "schulkind",
        "jugendarbeit", "kindergarten", "hort", "ganztagsbetreuung", "kinderpolitik",
        "frühkindliche förderung", "jugendamt",
    ],
    "education": [
        "bildung", "schule", "lehrer", "hochschule", "universität", "bafög",
        "berufsausbildung", "ausbildung", "studium", "bildungsgerechtigkeit",
        "bildungsfinanzierung", "digitalisierung schule", "lernmittelfreiheit",
        "inklusion", "sonderpädagogik", "ganztagsschule", "grundschule", "gymnasium",
        "gesamtschule", "bildungsföderalismus", "weiterbildung", "umschulung",
        "lebenslanges lernen", "volkshochschule", "meisterbrief", "duale ausbildung",
        "fachschule", "studiengebühren", "hochschulzulassung", "forschung",
        "wissenschaft", "ausbildungsplatz", "berufsschule", "bildungschancen",
        "chancengerechtigkeit", "frühkindliche bildung", "kitaqualität",
        "sprachförderung", "integration bildung", "lehramtsstudium", "quereinsteiger",
        "schulfinanzierung", "bildungsarmut", "pisa", "abitur", "hauptschule",
        "realschule", "schulpflicht", "schulabschluss", "nachhilfe", "förderunterricht",
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
    "work_transition": (
        "Die Zukunft der Arbeit in Deutschland — Mindestlohn, Tarifbindung, Fachkräftemangel "
        "und soziale Sicherung. Dieser Themenbereich umfasst Debatten über Mindestlöhne und "
        "Tarifverträge, Gewerkschaften und Arbeitgeber, Bürgergeld und Hartz-Reformen, "
        "Kurzarbeit und Beschäftigungssicherung, die Auswirkungen von Automatisierung und "
        "Digitalisierung auf den Arbeitsmarkt, Plattformarbeit und Scheinselbstständigkeit, "
        "Homeoffice, Qualifizierung und Umschulung sowie Fragen zu Lohngleichheit, "
        "Betriebsräten und Mitbestimmung."
    ),
    "defense": (
        "Die deutsche Verteidigungspolitik, Bundeswehr und NATO-Engagement. Dieser "
        "Themenbereich umfasst die Debatte um Wehrpflicht und Bundeswehrreform, "
        "Rüstungsausgaben und das NATO-Zwei-Prozent-Ziel, Rüstungsexporte und "
        "Waffenlieferungen, Auslandseinsätze der Bundeswehr, die Zeitenwende in der "
        "deutschen Sicherheitspolitik nach dem russischen Angriff auf die Ukraine, "
        "Cyberabwehr, Zivilschutz sowie Fragen zur Bündnisverteidigung und dem "
        "Artikel-5-Beistandsfall innerhalb der NATO."
    ),
    "family_children": (
        "Familienpolitik, Kinderbetreuung und Familienleistungen in Deutschland. Dieser "
        "Themenbereich umfasst Debatten über Kindergeld und Kinderfreibetrag, den Kita-Ausbau "
        "und Betreuungsplätze, Elterngeld und Elternzeit, die Vereinbarkeit von Familie und "
        "Beruf, Kinderarmut und Grundsicherung für Kinder, Jugendschutz und Jugendhilfe, "
        "Rechte und Wohlergehen von Kindern sowie frühkindliche Förderung. Auch Berichte "
        "über Hebammen, Geburtshilfe, Tagesmütter und Erzieher gehören dazu."
    ),
    "education": (
        "Das deutsche Bildungssystem von der Kita bis zur Hochschule und Weiterbildung. "
        "Dieser Themenbereich umfasst Debatten über Schulfinanzierung und "
        "Bildungsgerechtigkeit, BAföG und Studiengebühren, die duale Berufsausbildung, "
        "Digitalisierung in Schulen, Lehrkräftemangel und Quereinsteiger, "
        "Bildungsföderalismus, Inklusion und Sonderpädagogik, Ganztagsschulen, "
        "PISA-Studien sowie lebenslanges Lernen und Weiterbildung im Wandel der Arbeitswelt."
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
def call_llm(prompt: str, max_tokens: int = 300, system: str = "") -> str:
    """
    Unified LLM call — Groq primary (llama-3.3-70b-versatile), Claude Haiku fallback.
    Optional system message supported by both providers.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  Groq failed: {e} — trying Claude fallback")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            kwargs = {
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            print(f"  Claude fallback failed: {e}")

    raise RuntimeError("Kein LLM verfügbar — weder Groq noch Claude")


# ── DB Persistence ────────────────────────────────
def save_result(topic_id: str, result: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO analysis_results
            (topic_id, computed_at, article_count, result_json)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (topic_id) DO UPDATE SET
            computed_at   = EXCLUDED.computed_at,
            article_count = EXCLUDED.article_count,
            result_json   = EXCLUDED.result_json
    """, (
        topic_id,
        datetime.utcnow().isoformat(),
        result.get("article_count", 0),
        json.dumps(result, ensure_ascii=False),
    ))
    conn.commit()
    cur.close()
    conn.close()

    results_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "results")
    os.makedirs(results_dir, exist_ok=True)
    with open(os.path.join(results_dir, f"{topic_id}.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def load_cached_result(topic_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT result_json, computed_at FROM analysis_results WHERE topic_id = %s",
        (topic_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        result = json.loads(row["result_json"])
        result["cached_at"] = str(row["computed_at"])
        return result
    return None


# ── Step 1: Broad Retrieval ───────────────────────
def load_topic_articles(topic_id: str, days_back: int = 60) -> list[dict]:
    """Broad keyword retrieval — title AND text, limited to recent articles."""
    keywords = TOPIC_KEYWORDS.get(topic_id, [])
    if not keywords:
        return []

    # %% = literal % in psycopg2 SQL strings
    conditions = " OR ".join([
        f"(LOWER(title) LIKE '%%{kw}%%' OR LOWER(text) LIKE '%%{kw}%%')"
        for kw in keywords
    ])

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT id, title, text, source, source_id, bias,
               url, sentiment, emotion
        FROM articles
        WHERE ({conditions})
        AND word_count >= 10
        AND crawled_at >= NOW() - (%s * INTERVAL '1 day')
        ORDER BY crawled_at DESC
        LIMIT 800
    """, (days_back,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [dict(r) for r in rows]


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

        prompt = f"""Du filterst deutsche Nachrichtenartikel nach Themenrelevanz.

Thema: {topic_desc}

Artikeltitel (nummeriert):
{titles_list}

Welche dieser Artikel sind relevant?
Ein Artikel ist relevant wenn er:
1. DIREKT über das Thema berichtet ODER eng damit zusammenhängt, UND
2. einen DIREKTEN Bezug zu Deutschland hat — deutsche Politik, deutsche Gesellschaft, deutsche Institutionen oder nachweisbare Auswirkungen auf Deutschland.

Internationale Artikel ohne konkreten Deutschlandbezug ausschließen.
Antworte NUR mit einem JSON-Array der relevanten Artikelnummern.
Beispiel: [1, 3, 5, 7]
Falls keine relevant sind: []"""

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
    Identifies shared perspectives and controversial points across
    different media outlets using two separate LLM calls with
    dedicated system prompts for analytical depth.
    """
    topic_desc = TOPIC_DESCRIPTIONS.get(topic_id, topic_id)

    bias_samples = {}
    for article in articles:
        bias = article.get("bias", "unknown")
        if bias not in bias_samples:
            bias_samples[bias] = []
        if len(bias_samples[bias]) < 6:
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

    system_base = (
        "Du analysierst ausschließlich den deutschen Mediendiskurs. "
        "Beziehe dich nur auf Inhalte mit direktem Bezug zu Deutschland — "
        "deutsche Politik, deutsche Gesellschaft, deutsche Institutionen, "
        "Auswirkungen auf Deutschland. Internationale Ereignisse nur dann erwähnen "
        "wenn sie einen direkten nachweisbaren Einfluss auf Deutschland haben und "
        "deutsche Medien darüber im deutschen Kontext berichten. "
        "Vermeide generische internationale Aussagen."
    )

    system_shared = (
        system_base + " "
        "Identifiziere konkrete Themen, Ideen, Konzepte oder politische Positionen "
        "zu denen trotz unterschiedlicher politischer Ausrichtung eine erkennbare "
        "Übereinstimmung im deutschen Mediendiskurs besteht. Formuliere 2-3 präzise "
        "analytische Aussagen. Keine vagen Zusammenfassungen — konkrete inhaltliche "
        "Gemeinsamkeiten benennen. Keine Quellennennung. Fokus auf das Gesamtbild des Diskurses."
    )

    system_controversial = (
        system_base + " "
        "Identifiziere konkrete Spannungsfelder, Widersprüche und Konfliktlinien im "
        "deutschen Mediendiskurs zu diesem Thema. Wo prallen grundlegend unterschiedliche "
        "Weltbilder, Werte oder politische Konzepte aufeinander? Formuliere 2-3 präzise "
        "analytische Aussagen die die tatsächlichen Trennlinien benennen — nicht "
        "oberflächliche Meinungsverschiedenheiten sondern strukturelle Konflikte im Diskurs. "
        "Keine Quellennennung."
    )

    prompt_shared = f"""Thema: {topic_desc}

Artikeltitel nach politischer Ausrichtung der Medien:
{samples_text}

Welche inhaltlichen Gemeinsamkeiten zeigen sich im deutschen Mediendiskurs zu diesem Thema?
Antworte auf Deutsch in 2-3 präzisen analytischen Sätzen. Nur Fließtext, kein JSON, keine Aufzählung."""

    prompt_controversial = f"""Thema: {topic_desc}

Artikeltitel nach politischer Ausrichtung der Medien:
{samples_text}

Welche strukturellen Konfliktlinien und Spannungsfelder zeigen sich im deutschen Mediendiskurs zu diesem Thema?
Antworte auf Deutsch in 2-3 präzisen analytischen Sätzen. Nur Fließtext, kein JSON, keine Aufzählung."""

    shared = "Synthese nicht verfügbar."
    controversial = "Synthese nicht verfügbar."

    try:
        shared = call_llm(prompt_shared, max_tokens=500, system=system_shared).strip()
        print(f"  ✓ Shared synthesis generated ({len(shared)} chars)")
    except Exception as e:
        print(f"  ⚠ Shared synthesis failed: {e}")

    try:
        controversial = call_llm(prompt_controversial, max_tokens=500, system=system_controversial).strip()
        print(f"  ✓ Controversial synthesis generated ({len(controversial)} chars)")
    except Exception as e:
        print(f"  ⚠ Controversial synthesis failed: {e}")

    return {
        "shared_perspectives": shared,
        "controversial_points": controversial,
    }


# ── Main Analysis ─────────────────────────────────
def analyze_topic(topic_id: str) -> dict:
    """Full Medienspiegel analysis pipeline."""
    print(f"\n🔍 Analyzing: {topic_id}")
    candidates = load_topic_articles(topic_id, days_back=60)
    print(f"  → {len(candidates)} candidates retrieved (60 days)")

    bias_groups = {a.get("bias") for a in candidates if a.get("bias") and a.get("bias") != "unknown"}
    if len(bias_groups) < 3:
        print(f"  ⚠ Only {len(bias_groups)} bias group(s) — expanding to 180 days")
        candidates = load_topic_articles(topic_id, days_back=180)
        print(f"  → {len(candidates)} candidates after expansion")

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


def compute_all_topics():
    """Pre-computes and caches all topic analyses. Called by GitHub Actions."""
    print("\nDiskursraum — Medienspiegel Analysis")
    print(f"   Topics: {list(TOPICS.keys())}\n")
    print(f"   LLM Provider: {os.getenv('LLM_PROVIDER', 'groq').upper()}\n")

    success = 0
    failed = 0

    for topic_id in TOPICS.keys():
        try:
            result = analyze_topic(topic_id)
            if "error" not in result:
                save_result(topic_id, result)
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