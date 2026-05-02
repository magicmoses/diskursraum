"""
analyze_historical.py — Cross-Year Historical Analysis

Reads all manifestos_{year}.json files and computes:
  1. Structural analysis: program length, lexical density per party per year
  2. Semantic trajectories: PCA on party embeddings across years
  3. Pairwise distance matrix per year
  4. Top-5 election topics per year via LLM
  5. Bridging score time series (5 stable parties)

Output: data/results/historical_analysis.json

Run:
  python analyze_historical.py
  python analyze_historical.py --skip-llm
"""

import os
import sys
import json
import re
import numpy as np
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

BASE_DIR = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = BASE_DIR / "data" / "results"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

AVAILABLE_YEARS = [2005, 2009, 2013, 2017, 2021, 2025]

PARTIES = {
    "cdu_csu": {"name": "CDU/CSU",              "color": "#000000"},
    "spd":     {"name": "SPD",                   "color": "#E3000F"},
    "gruene":  {"name": "Bündnis 90/Die Grünen", "color": "#1AA037"},
    "fdp":     {"name": "FDP",                   "color": "#FFED00"},
    "afd":     {"name": "AfD",                   "color": "#009EE0"},
    "linke":   {"name": "Die Linke",             "color": "#BE3075"},
}

HISTORICAL_EVENTS = [
    # 2005
    {"year": 2005, "label": "Hartz IV tritt in Kraft",         "category": "economy"},
    {"year": 2005, "label": "Große Koalition CDU/SPD",         "category": "politics"},
    # 2007-2009
    {"year": 2007, "label": "Einführung Mindestlohn (Branchen)","category": "economy"},
    {"year": 2008, "label": "Weltfinanzkrise",                  "category": "economy"},
    {"year": 2009, "label": "Eurokrise beginnt",                "category": "economy"},
    # 2010-2013
    {"year": 2011, "label": "Fukushima — Atomausstieg",         "category": "energy"},
    {"year": 2011, "label": "Arabischer Frühling",              "category": "foreign"},
    {"year": 2013, "label": "NSA-Abhörskandal",                 "category": "digital"},
    {"year": 2013, "label": "AfD gegründet",                    "category": "politics"},
    # 2014-2017
    {"year": 2014, "label": "Ukrainekrieg (Krim-Annexion)",     "category": "foreign"},
    {"year": 2015, "label": "Flüchtlingskrise",                 "category": "migration"},
    {"year": 2016, "label": "Brexit",                           "category": "foreign"},
    {"year": 2017, "label": "AfD erstmals im Bundestag",        "category": "politics"},
    # 2018-2021
    {"year": 2018, "label": "Fridays for Future",               "category": "climate"},
    {"year": 2020, "label": "Corona-Pandemie",                  "category": "health"},
    {"year": 2021, "label": "Ampelkoalition",                   "category": "politics"},
    {"year": 2021, "label": "Flutkatastrophe Ahrtal",           "category": "climate"},
    # 2022-2025
    {"year": 2022, "label": "Russlands Angriff auf Ukraine",    "category": "foreign"},
    {"year": 2022, "label": "Energiekrise",                     "category": "energy"},
    {"year": 2023, "label": "Letztes AKW abgeschaltet",         "category": "energy"},
    {"year": 2024, "label": "Ampel-Bruch",                      "category": "politics"},
    {"year": 2025, "label": "CDU/CSU-geführte Koalition",       "category": "politics"},
]


# ── 1. Structural Analysis ────────────────────────
def analyze_structure(year: int) -> dict:
    """
    Loads ALL chunks from ChromaDB (not just top_chunks from JSON)
    for accurate word count and lexical density per party.
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(f"manifestos_{year}")
    except Exception:
        print(f"  ChromaDB manifestos_{year} not found — skipping structure")
        return {}

    structural = {}
    for party_id, party_info in PARTIES.items():
        try:
            results = collection.get(
                where={"party_id": party_id},
                include=["documents"],
            )
            if not results["documents"]:
                continue

            all_text = " ".join(results["documents"])
            words = all_text.split()
            total = len(words)
            unique = len(set(w.lower() for w in words))

            structural[party_id] = {
                "party_name": party_info["name"],
                "total_words": total,
                "unique_words": unique,
                "lexical_density": round(unique / total, 4) if total > 0 else 0,
                "chunk_count": len(results["documents"]),
            }
        except Exception:
            continue

    return structural


# ── 2. Pairwise Distance Matrix ───────────────────
def compute_distance_matrix(manifesto_data: dict) -> dict:
    """Aggregates pairwise similarity across all topics."""
    pairwise_all = defaultdict(list)

    for topic_data in manifesto_data.get("results", {}).values():
        for pair, sim in topic_data.get("bridging", {}).get("pairwise_similarity", {}).items():
            pairwise_all[pair].append(sim)

    return {
        pair: round(float(np.mean(sims)), 4)
        for pair, sims in pairwise_all.items()
    }


# ── 3. PCA Trajectories ───────────────────────────
def compute_pca_trajectories(years_found: list) -> dict:
    """
    Loads mean embeddings per party per year from ChromaDB,
    stacks them and runs PCA once for all years together.
    This gives a shared 2D space where movement is directly comparable.
    """
    try:
        import chromadb
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import normalize
    except ImportError:
        print("  PCA skipped — sklearn or chromadb not available")
        return {}

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    embeddings = []
    labels = []  # (party_id, year)

    for year in years_found:
        try:
            collection = client.get_collection(f"manifestos_{year}")
        except Exception:
            continue

        for party_id in PARTIES.keys():
            try:
                results = collection.get(
                    where={"party_id": party_id},
                    include=["embeddings"],
                )
                if results["embeddings"]:
                    mean_emb = np.mean(results["embeddings"], axis=0)
                    embeddings.append(mean_emb)
                    labels.append((party_id, year))
            except Exception:
                continue

    if len(embeddings) < 3:
        print("  Not enough data for PCA")
        return {}

    coords = PCA(n_components=2).fit_transform(
        normalize(np.array(embeddings))
    )

    trajectories = defaultdict(list)
    for i, (party_id, year) in enumerate(labels):
        trajectories[party_id].append({
            "year": year,
            "x": round(float(coords[i][0]), 4),
            "y": round(float(coords[i][1]), 4),
        })

    for party_id in trajectories:
        trajectories[party_id].sort(key=lambda p: p["year"])

    return {
        "trajectories": dict(trajectories),
        "party_metadata": {
            pid: {"name": PARTIES[pid]["name"], "color": PARTIES[pid]["color"]}
            for pid in trajectories
        },
    }


# ── 4. Election Topics via LLM ────────────────────
def get_election_topics(year: int) -> list[str]:
    """Top-5 Wahlthemen pro Jahr — ein LLM Call pro Jahr."""
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""Was waren die 5 dominantesten politischen Themen der deutschen Bundestagswahl {year}?
Kurze Schlagworte (1-3 Wörter), keine Erklärungen.
Antworte NUR mit JSON-Array: ["Thema1", "Thema2", "Thema3", "Thema4", "Thema5"]"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100,
        )
        raw = re.sub(r'```json|```', '', response.choices[0].message.content.strip()).strip()
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())[:5]
    except Exception as e:
        print(f"  LLM failed for {year}: {e}")
    return []


# ── 5. Bridging Time Series ───────────────────────
def compute_bridging_timeseries(all_years_data: dict) -> dict:
    """
    Mean bridging score per party per year across all topics.
    Uses only the 5 stable parties for cross-year comparability.
    AfD included separately (2013+) for the "AfD effect" analysis.
    """
    stable = ["cdu_csu", "spd", "gruene", "fdp", "linke"]
    timeseries = defaultdict(dict)

    for year, data in all_years_data.items():
        party_scores = defaultdict(list)

        for topic_data in data.get("results", {}).values():
            for party_id, score in topic_data.get("bridging", {}).get("bridging_scores", {}).items():
                party_scores[party_id].append(score)

        for party_id, scores in party_scores.items():
            timeseries[party_id][year] = round(float(np.mean(scores)), 4)

    return {
        "stable_parties": {
            pid: timeseries[pid]
            for pid in stable
            if pid in timeseries
        },
        "afd": timeseries.get("afd", {}),
        "note": "stable_parties: 5 Parteien in allen Jahren. afd: separat ab 2013.",
    }


# ── Main ──────────────────────────────────────────
def run_analysis(skip_llm: bool = False):
    print("Diskursraum — Historical Analysis")

    all_years_data = {}
    years_found = []

    for year in AVAILABLE_YEARS:
        path = RESULTS_DIR / f"manifestos_{year}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                all_years_data[year] = json.load(f)
            years_found.append(year)
            print(f"Loaded manifestos_{year}.json")
        else:
            print(f"Missing: manifestos_{year}.json")

    if not years_found:
        print("No data found — run pipeline first")
        return

    print(f"\nAnalyzing years: {years_found}\n")

    print("Step 1: Structural Analysis (from ChromaDB)")
    structural = {year: analyze_structure(year) for year in years_found}

    print("\nStep 2: Pairwise Distance Matrices")
    matrices = {year: compute_distance_matrix(all_years_data[year]) for year in years_found}

    print("\nStep 3: PCA Trajectories")
    pca = compute_pca_trajectories(years_found)

    print("\nStep 4: Election Topics")
    topics = {}
    if not skip_llm:
        for year in years_found:
            topics[year] = get_election_topics(year)
            print(f"  {year}: {topics[year]}")
    else:
        print("  Skipped")

    print("\nStep 5: Bridging Time Series")
    bridging_ts = compute_bridging_timeseries(all_years_data)

    output = {
        "years_analyzed": years_found,
        "historical_events": HISTORICAL_EVENTS,
        "structural_analysis": {str(y): v for y, v in structural.items()},
        "distance_matrices": {str(y): v for y, v in matrices.items()},
        "pca_trajectories": pca,
        "election_topics": {str(y): v for y, v in topics.items()},
        "bridging_timeseries": bridging_ts,
        "graphs_by_year": {
            str(year): all_years_data[year].get("graph", {})
            for year in years_found
        },
    }

    path = RESULTS_DIR / "historical_analysis.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved: historical_analysis.json ({path.stat().st_size // 1024}KB)")
    print("Done")


if __name__ == "__main__":
    run_analysis(skip_llm="--skip-llm" in sys.argv)