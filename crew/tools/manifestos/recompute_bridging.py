"""
recompute_bridging.py — Neuberechnung Bridging Scores (zwei-Signal-Modell)

Liest Embeddings direkt aus ChromaDB — keine LLM-Aufrufe nötig.
Filtert Chunks per Thema via Keyword-Matching.
Aktualisiert manifestos_{year}.json und rebuildet historical_analysis.json.

Usage:
  python recompute_bridging.py                 # alle Jahre
  python recompute_bridging.py 2025            # einzelnes Jahr
  python recompute_bridging.py 2025 2021       # mehrere Jahre
  python recompute_bridging.py --skip-history  # ohne historical rebuild
"""

import sys
import os
import json
import subprocess
import numpy as np
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

BASE_DIR    = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = BASE_DIR / "data" / "results"
CHROMA_DIR  = BASE_DIR / "data" / "chroma_db"

AVAILABLE_YEARS = [2005, 2009, 2013, 2017, 2021, 2025]

PARTIES = {
    "cdu_csu": {"name": "CDU/CSU",              "color": "#000000"},
    "spd":     {"name": "SPD",                   "color": "#E3000F"},
    "gruene":  {"name": "Bündnis 90/Die Grünen", "color": "#1AA037"},
    "fdp":     {"name": "FDP",                   "color": "#FFED00"},
    "afd":     {"name": "AfD",                   "color": "#009EE0"},
    "linke":   {"name": "Die Linke",             "color": "#BE3075"},
}

TOPIC_KEYWORDS = {
    "migration":         ["migration", "asyl", "flüchtlinge", "einwanderung", "abschiebung", "integration", "zuwanderung", "grenzschutz", "geflüchtete", "aufenthaltsrecht"],
    "energy_transition": ["energiewende", "erneuerbare", "atomkraft", "kernenergie", "windenergie", "solarenergie", "kohleausstieg", "klimaschutz", "energiepolitik", "co2"],
    "retirement":        ["rente", "rentenpolitik", "rentenreform", "altersvorsorge", "rentenalter", "rentenniveau", "altersarmut", "rentenversicherung", "generationenvertrag"],
    "digitalization":    ["digitalisierung", "künstliche intelligenz", "ki", "digitale transformation", "datenschutz", "cybersicherheit", "e-government", "breitband"],
    "work_transition":   ["arbeitsmarkt", "mindestlohn", "tarifvertrag", "fachkräftemangel", "kurzarbeit", "homeoffice", "beschäftigung", "gewerkschaft", "vollbeschäftigung", "arbeitnehmer"],
    "defense":           ["bundeswehr", "verteidigung", "nato", "militär", "rüstung", "wehrpflicht", "auslandseinsatz", "landesverteidigung", "sicherheitspolitik", "verteidigungshaushalt"],
    "family_children":   ["familie", "kinder", "kindergeld", "elterngeld", "kita", "kindertagesstätte", "kinderarmut", "familienpolitik", "vereinbarkeit", "betreuung"],
    "education":         ["bildung", "schule", "hochschule", "universität", "ausbildung", "weiterbildung", "lebenslanges lernen", "lehrermangel", "bildungsfinanzierung", "studium"],
}

TOPIC_LABELS = {
    "migration":         "Migration & Asylpolitik",
    "energy_transition": "Energiewende",
    "retirement":        "Rente & Altersvorsorge",
    "digitalization":    "Digitale Transformation & KI",
    "work_transition":   "Arbeit im Wandel",
    "defense":           "Verteidigung & Militär",
    "family_children":   "Für Familien & Kinder",
    "education":         "Bildung & lebenslanges Lernen",
}

REMOVED_TOPICS = ["wealth_tax"]


# ── Category Distributions ────────────────────────
def load_cat_distributions(year: int) -> dict:
    """Loads ManifestoBERTa category distributions per party from JSON."""
    path = RESULTS_DIR / f"category_distribution_{year}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for party_id, pdata in data.get("parties", {}).items():
        dist_raw = pdata.get("distribution", {}).get("distribution", {})
        result[party_id] = {cat: v["count"] for cat, v in dist_raw.items()}
    return result


# ── ChromaDB Retrieval ────────────────────────────
def filter_by_keywords(chunks: list, keywords: list) -> tuple:
    """Keyword-based relevance filter. Returns (filtered_chunks, indices)."""
    filtered, indices = [], []
    for i, chunk in enumerate(chunks):
        text = chunk.lower()
        if any(kw in text for kw in keywords):
            filtered.append(chunk)
            indices.append(i)
    return filtered, indices


def get_topic_embeddings(
    year: int,
    topic_id: str,
    keywords: list,
    min_chunks: int = 3,
) -> dict:
    """
    Loads topic-filtered embeddings per party directly from ChromaDB.
    Falls back to all chunks if keyword filter yields too few results.
    Returns {party_id: (chunks, embeddings_array)}.
    """
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        collection = client.get_collection(f"manifestos_{year}")
    except Exception as e:
        print(f"    Collection manifestos_{year} not found: {e}")
        return {}

    result = {}
    for party_id in PARTIES:
        try:
            res = collection.get(
                where={"party_id": party_id},
                include=["documents", "embeddings"],
            )
            all_chunks = res.get("documents") or []
            embs_raw   = res.get("embeddings")

            if not all_chunks or embs_raw is None or len(embs_raw) == 0:
                continue

            all_embs_np = np.array(embs_raw)

            filtered, indices = filter_by_keywords(all_chunks, keywords)

            if len(filtered) < min_chunks:
                chunks_out = all_chunks
                embs_out   = all_embs_np
                print(f"      {party_id}: {len(all_chunks)} chunks (fallback — too few keyword matches)")
            else:
                chunks_out = filtered
                embs_out   = all_embs_np[indices]
                print(f"      {party_id}: {len(filtered)}/{len(all_chunks)} chunks relevant")

            result[party_id] = (chunks_out, embs_out)

        except Exception as e:
            print(f"      {party_id} failed: {e}")

    return result


# ── Per-Year Recomputation ────────────────────────
def recompute_year(year: int, cat_dist: dict, verbose: bool = True) -> bool:
    from bridging_scorer import compute_pair_scores, compute_betweenness_bridging
    from graph_builder import build_party_graph

    path = RESULTS_DIR / f"manifestos_{year}.json"
    if not path.exists():
        print(f"  manifestos_{year}.json not found — skipping")
        return False

    data = json.loads(path.read_text(encoding="utf-8"))
    results = data.get("results", {})

    for topic_id, keywords in TOPIC_KEYWORDS.items():
        if verbose:
            print(f"\n  [{TOPIC_LABELS[topic_id]}]")

        topic_data = get_topic_embeddings(year, topic_id, keywords)
        if len(topic_data) < 2:
            print(f"    Not enough parties ({len(topic_data)}) — skipping")
            continue

        party_chunks     = {p: chunks for p, (chunks, _) in topic_data.items()}
        party_embeddings = {p: embs   for p, (_, embs)   in topic_data.items()}

        pair_scores = compute_pair_scores(
            party_chunks=party_chunks,
            party_embeddings=party_embeddings,
            party_cat_distributions=cat_dist or None,
        )

        if not pair_scores:
            print(f"    Pair score computation failed — skipping")
            continue

        bridging = compute_betweenness_bridging(pair_scores, PARTIES)
        bridging["topic_id"] = topic_id
        bridging["pairwise_similarity"] = pair_scores

        if topic_id in results:
            results[topic_id]["bridging"] = bridging
        else:
            results[topic_id] = {
                "topic_id": topic_id,
                "topic_label": TOPIC_LABELS[topic_id],
                "parties": {},
                "bridging": bridging,
                "synthesis": {},
            }

        most   = bridging.get("most_bridging_party_name", "—")
        m_pid  = bridging.get("most_bridging_party")
        m_score = bridging["bridging_scores"].get(m_pid, 0.0) if m_pid else 0.0
        print(f"    Most bridging: {most} ({m_score:.4f})")

        # Spread check
        vals = list(pair_scores.values())
        if vals:
            print(f"    Pair score range: {min(vals):.4f} – {max(vals):.4f}")

    for removed in REMOVED_TOPICS:
        if removed in results:
            del results[removed]
            print(f"  Removed deprecated topic: {removed}")

    print(f"\n  Building graph...")
    graph = build_party_graph(results, PARTIES, output_dir=RESULTS_DIR)
    print(f"  {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    print(f"  Overall most bridging: {graph.get('most_bridging_party_name')}")

    data["results"]     = results
    data["topics"]      = list(TOPIC_KEYWORDS.keys())
    data["graph"]       = graph
    data["computed_at"] = datetime.utcnow().isoformat()

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Saved manifestos_{year}.json")
    return True


# ── Validation ────────────────────────────────────
def print_validation(years_processed: list):
    """Sanity checks on recomputed scores."""
    print("\n" + "=" * 60)
    print("VALIDIERUNG")
    print("=" * 60)

    for year in years_processed:
        path = RESULTS_DIR / f"manifestos_{year}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        results = data.get("results", {})

        print(f"\n  Jahr {year}")

        # Aggregate pairwise scores across all topics
        pair_acc = {}
        for topic_data in results.values():
            for pair, score in topic_data.get("bridging", {}).get("pairwise_similarity", {}).items():
                pair_acc.setdefault(pair, []).append(score)

        if not pair_acc:
            print("    Keine Daten")
            continue

        pair_means = {k: round(float(np.mean(v)), 4) for k, v in pair_acc.items()}
        sorted_pairs = sorted(pair_means.items(), key=lambda x: x[1], reverse=True)

        print(f"    Ähnlichste Paare:   " + ", ".join(
            f"{p} ({s:.3f})" for p, s in sorted_pairs[:3]
        ))
        print(f"    Unähnlichste Paare: " + ", ".join(
            f"{p} ({s:.3f})" for p, s in sorted_pairs[-3:]
        ))

        all_vals = list(pair_means.values())
        print(f"    Spread: {min(all_vals):.4f} - {max(all_vals):.4f} "
              f"(D = {max(all_vals) - min(all_vals):.4f})")

        # Bridging scores
        bs_acc = {}
        for topic_data in results.values():
            for pid, score in topic_data.get("bridging", {}).get("bridging_scores", {}).items():
                bs_acc.setdefault(pid, []).append(score)
        bs_means = {p: round(float(np.mean(v)), 4) for p, v in bs_acc.items()}
        sorted_bs = sorted(bs_means.items(), key=lambda x: x[1], reverse=True)
        print(f"    Bridging-Scores: " + ", ".join(
            f"{PARTIES.get(p, {}).get('name', p)} {s:.3f}" for p, s in sorted_bs
        ))


# ── Main ──────────────────────────────────────────
def main():
    args = sys.argv[1:]
    skip_history = "--skip-history" in args
    years = [int(a) for a in args if a.isdigit() and int(a) in AVAILABLE_YEARS]
    if not years:
        years = AVAILABLE_YEARS

    print(f"Diskursraum — Bridging Score Neuberechnung")
    print(f"Jahre: {years}")
    print(f"Modell: 40% semantisch (PCA) + 60% thematisch (Jaccard)")
    print()

    processed = []
    for year in years:
        print(f"\n{'=' * 50}")
        print(f"Jahr {year}")
        print(f"{'=' * 50}")

        cat_dist = load_cat_distributions(year)
        if cat_dist:
            print(f"Kategorienverteilungen geladen: {list(cat_dist.keys())}")
        else:
            print(f"Keine Kategorienverteilungen — nur Signal 1 (semantisch)")

        ok = recompute_year(year, cat_dist)
        if ok:
            processed.append(year)

    if processed:
        print_validation(processed)

    if not skip_history and processed:
        print(f"\n{'=' * 50}")
        print("Rebuilding historical_analysis.json")
        print(f"{'=' * 50}")
        script = Path(__file__).parent / "analyze_historical.py"
        result = subprocess.run(
            [sys.executable, str(script), "--skip-llm"],
            cwd=str(Path(__file__).parent),
            capture_output=True, text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"analyze_historical.py failed:\n{result.stderr}")
        else:
            print("historical_analysis.json updated")

    print(f"\nFertig. {len(processed)}/{len(years)} Jahre verarbeitet.")


if __name__ == "__main__":
    main()
