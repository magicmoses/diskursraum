"""
analyze_historical.py — Cross-Year Historical Analysis

Steps:
  1. Structural analysis: program length + lexical density (ChromaDB)
  2. Pairwise distance matrix per year
  3. PCA trajectories: shared 2D semantic space across years
  4. Election topics per year via LLM (1 call per year)
  5. Bridging score time series (5 stable parties + AfD separate)
  6. ManifestoBERTa: pos/neg ratio, policy emphasis, clarity, overlap trends
  7. Election results + bridging/vote correlation

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

BASE_DIR   = Path(__file__).parent.parent.parent.parent
RESULTS_DIR = BASE_DIR / "data" / "results"
CHROMA_DIR  = BASE_DIR / "data" / "chroma_db"

AVAILABLE_YEARS = [2005, 2009, 2013, 2017, 2021, 2025]
STABLE_PARTIES  = ["cdu_csu", "spd", "gruene", "fdp", "linke"]

PARTIES = {
    "cdu_csu": {"name": "CDU/CSU",              "color": "#000000"},
    "spd":     {"name": "SPD",                   "color": "#E3000F"},
    "gruene":  {"name": "Bündnis 90/Die Grünen", "color": "#1AA037"},
    "fdp":     {"name": "FDP",                   "color": "#FFED00"},
    "afd":     {"name": "AfD",                   "color": "#009EE0"},
    "linke":   {"name": "Die Linke",             "color": "#BE3075"},
}

CATEGORY_GROUPS = {
    "external_relations": [101,102,103,104,105,106,107,108],
    "freedom_democracy":  [201,202,203,204],
    "political_system":   [301,302,303,304,305],
    "economy":            [401,402,403,404,405,406,407,408,409,410],
    "welfare":            [501,502,503,504,505,506,507],
    "fabric_of_society":  [601,602,603,604,605,606,607,608],
    "social_groups":      [701,702,703,704],
}

# Precomputed lookup: cat_code → group
_CAT_TO_GROUP = {
    code: group
    for group, codes in CATEGORY_GROUPS.items()
    for code in codes
}

HISTORICAL_EVENTS = [
    {"year": 2005, "label": "Hartz IV tritt in Kraft",          "category": "economy"},
    {"year": 2005, "label": "Große Koalition CDU/SPD",          "category": "politics"},
    {"year": 2007, "label": "Einführung Mindestlohn (Branchen)", "category": "economy"},
    {"year": 2008, "label": "Weltfinanzkrise",                   "category": "economy"},
    {"year": 2009, "label": "Eurokrise beginnt",                 "category": "economy"},
    {"year": 2011, "label": "Fukushima — Atomausstieg",          "category": "energy"},
    {"year": 2011, "label": "Arabischer Frühling",               "category": "foreign"},
    {"year": 2013, "label": "NSA-Abhörskandal",                  "category": "digital"},
    {"year": 2013, "label": "AfD gegründet",                     "category": "politics"},
    {"year": 2014, "label": "Ukrainekrieg (Krim-Annexion)",      "category": "foreign"},
    {"year": 2015, "label": "Flüchtlingskrise",                  "category": "migration"},
    {"year": 2016, "label": "Brexit",                            "category": "foreign"},
    {"year": 2017, "label": "AfD erstmals im Bundestag",         "category": "politics"},
    {"year": 2018, "label": "Fridays for Future",                "category": "climate"},
    {"year": 2020, "label": "Corona-Pandemie",                   "category": "health"},
    {"year": 2021, "label": "Ampelkoalition",                    "category": "politics"},
    {"year": 2021, "label": "Flutkatastrophe Ahrtal",            "category": "climate"},
    {"year": 2022, "label": "Russlands Angriff auf Ukraine",     "category": "foreign"},
    {"year": 2022, "label": "Energiekrise",                      "category": "energy"},
    {"year": 2023, "label": "Letztes AKW abgeschaltet",          "category": "energy"},
    {"year": 2024, "label": "Ampel-Bruch",                       "category": "politics"},
    {"year": 2025, "label": "CDU/CSU-geführte Koalition",        "category": "politics"},
]


# ── Helpers ───────────────────────────────────────
def _chroma():
    import chromadb
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _mean(values: list) -> float | None:
    return round(float(np.mean(values)), 4) if values else None


# ── 1. Structural Analysis ────────────────────────
def analyze_structure(years_found: list) -> dict:
    """Word count + Type-Token-Ratio from all ChromaDB chunks."""
    client = _chroma()
    result = {}
    for year in years_found:
        try:
            col = client.get_collection(f"manifestos_{year}")
        except Exception:
            continue
        year_data = {}
        for pid, info in PARTIES.items():
            try:
                docs = col.get(where={"party_id": pid}, include=["documents"])["documents"]
                if not docs:
                    continue
                words = " ".join(docs).split()
                total, unique = len(words), len(set(w.lower() for w in words))
                year_data[pid] = {
                    "party_name": info["name"],
                    "total_words": total,
                    "unique_words": unique,
                    "lexical_density": round(unique / total, 4) if total else 0,
                    "chunk_count": len(docs),
                }
            except Exception:
                continue
        result[str(year)] = year_data
        print(f"  {year}: {list(year_data.keys())}")
    return result


# ── 2. Pairwise Distance Matrix ───────────────────
def compute_distance_matrices(all_years_data: dict) -> dict:
    """Mean cosine similarity per party pair per year across all topics."""
    result = {}
    for year, data in all_years_data.items():
        pairs = defaultdict(list)
        for topic in data.get("results", {}).values():
            for pair, sim in topic.get("bridging", {}).get("pairwise_similarity", {}).items():
                pairs[pair].append(sim)
        result[str(year)] = {p: round(float(np.mean(s)), 4) for p, s in pairs.items()}
        print(f"  {year}: {len(result[str(year)])} pairs")
    return result


# ── 3. PCA Trajectories ───────────────────────────
def compute_pca_trajectories(years_found: list) -> dict:
    """
    Single PCA on all party-year mean embeddings.
    Shared 2D space — movement directly comparable across years.

    Coordinates normalized to [-1, 1] for consistent frontend scaling.
    Check explained_variance to assess how much variance is captured...
    Rule of thumb: >50% combined is acceptable for 768-dim embeddings.
    """
    try:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import normalize, MinMaxScaler
    except ImportError:
        return {}

    client = _chroma()
    embeddings, labels = [], []

    for year in years_found:
        try:
            col = client.get_collection(f"manifestos_{year}")
        except Exception:
            continue
        for pid in PARTIES:
            try:
                res = col.get(where={"party_id": pid}, include=["embeddings"])
                if res["embeddings"] is not None and len(res["embeddings"]) > 0:
                    embeddings.append(np.mean(res["embeddings"], axis=0))
                    labels.append((pid, year))
            except Exception:
                continue

    if len(embeddings) < 3:
        return {}

    pca_model = PCA(n_components=2)
    coords = pca_model.fit_transform(normalize(np.array(embeddings)))

    # Normalize to [-1, 1] makes frontend scaling trivial
    # and keeps coordinates comparable if we add more years later
    scaler = MinMaxScaler(feature_range=(-1, 1))
    coords = scaler.fit_transform(coords)

    trajectories = defaultdict(list)
    for i, (pid, year) in enumerate(labels):
        trajectories[pid].append({
            "year": year,
            "x": round(float(coords[i][0]), 4),
            "y": round(float(coords[i][1]), 4),
        })

    for pid in trajectories:
        trajectories[pid].sort(key=lambda p: p["year"])

    explained = [round(float(v), 4) for v in pca_model.explained_variance_ratio_]
    print(f"  {len(trajectories)} parties, {len(embeddings)} data points")
    print(f"  Explained variance: PC1={explained[0]:.1%}, PC2={explained[1]:.1%}, total={sum(explained):.1%}")

    return {
        "trajectories": dict(trajectories),
        "explained_variance": explained,
        "party_metadata": {
            pid: {"name": PARTIES[pid]["name"], "color": PARTIES[pid]["color"]}
            for pid in trajectories
        },
    }


# ── 4. Election Topics via LLM ────────────────────
def get_election_topics(years_found: list) -> dict:
    """One Groq call per year — 6 calls total."""
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    result = {}
    for year in years_found:
        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content":
                    f"Top 5 politische Themen der deutschen Bundestagswahl {year}. "
                    f"Kurze Schlagworte. NUR JSON-Array: [\"T1\",\"T2\",\"T3\",\"T4\",\"T5\"]"
                }],
                temperature=0.1, max_tokens=100,
            )
            raw = re.sub(r'```json|```', '', resp.choices[0].message.content).strip()
            match = re.search(r'\[.*?\]', raw, re.DOTALL)
            result[str(year)] = json.loads(match.group())[:5] if match else []
            print(f"  {year}: {result[str(year)]}")
        except Exception as e:
            print(f"  {year} failed: {e}")
            result[str(year)] = []
    return result


# ── 5. Bridging Time Series ───────────────────────
def compute_bridging_timeseries(all_years_data: dict) -> dict:
    """Mean bridging score per party per year. AfD separate (2013+)."""
    ts = defaultdict(dict)
    for year, data in all_years_data.items():
        scores = defaultdict(list)
        for topic in data.get("results", {}).values():
            for pid, s in topic.get("bridging", {}).get("bridging_scores", {}).items():
                scores[pid].append(s)
        for pid, s in scores.items():
            ts[pid][str(year)] = round(float(np.mean(s)), 4)
    return {
        "stable_parties": {pid: ts[pid] for pid in STABLE_PARTIES if pid in ts},
        "afd": ts.get("afd", {}),
        "note": "5-party stable set for cross-year comparability. AfD separate (2013+).",
    }


# ── 6. ManifestoBERTa Category Analysis ──────────
def analyze_categories(years_found: list) -> dict:
    """
    Loads category_distribution_{year}.json and computes:
    1. Positive/negative ratio per category per party
    2. Policy emphasis: % of program per category group
    3. Programmatic clarity: mean confidence per party (if chunk_confidences available)
    4. Category overlap over time: convergence/divergence per party pair

    ManifestoBERTa label format: "411 - Technology and Infrastructure: Positive"
    Pos/neg split on ": Positive" / ": Negative" suffix.
    Group mapping on numeric code prefix before " - ".
    """
    years_data = {
        year: _load_json(RESULTS_DIR / f"category_distribution_{year}.json")
        for year in years_found
        if (RESULTS_DIR / f"category_distribution_{year}.json").exists()
    }
    if not years_data:
        return {}

    pos_neg_by_year, emphasis_by_year, clarity_by_year = {}, {}, {}

    for year, data in years_data.items():
        pos_neg, emphasis, clarity = {}, {}, {}

        for pid, pdata in data.get("parties", {}).items():
            dist = pdata.get("distribution", {}).get("distribution", {})
            pos, neg, groups = defaultdict(int), defaultdict(int), defaultdict(int)
            total = sum(v["count"] for v in dist.values())

            for cat, v in dist.items():
                count = v["count"]

                # Pos/neg split — label format: "411 - Label: Positive"
                if ": Positive" in cat:
                    base = cat.split(":")[0].strip()
                    pos[base] += count
                elif ": Negative" in cat:
                    base = cat.split(":")[0].strip()
                    neg[base] += count

                # Group mapping — extract numeric code before " - "
                try:
                    cat_code = int(cat.split(" - ")[0].strip())
                    group = _CAT_TO_GROUP.get(cat_code)
                    if group:
                        groups[group] += count
                except (ValueError, AttributeError):
                    pass

            pos_neg[pid] = {
                cat: {
                    "positive": pos[cat], "negative": neg[cat],
                    "ratio": round(pos[cat] / (pos[cat] + neg[cat]), 4)
                    if (pos[cat] + neg[cat]) > 0 else None,
                }
                for cat in set(pos) | set(neg)
            }
            emphasis[pid] = {
                g: round(c * 100 / total, 2) if total else 0
                for g, c in groups.items()
            }

            # Clarity — only if chunk_confidences was stored (requires rerun of classify_chunks)
            confs = pdata.get("chunk_confidences", [])
            if confs:
                m = float(np.mean(confs))
                clarity[pid] = {
                    "mean_confidence": round(m, 4),
                    "std_confidence": round(float(np.std(confs)), 4),
                    "clarity_label": "klar" if m > 0.65 else "moderat" if m > 0.45 else "vage",
                }

        pos_neg_by_year[str(year)]  = pos_neg
        emphasis_by_year[str(year)] = emphasis
        clarity_by_year[str(year)]  = clarity

    # Category overlap over time
    overlap = defaultdict(dict)
    for year, data in years_data.items():
        pids = list(data.get("parties", {}).keys())
        for i, p1 in enumerate(pids):
            for p2 in pids[i+1:]:
                dist1 = data["parties"][p1].get("distribution", {}).get("distribution", {})
                dist2 = data["parties"][p2].get("distribution", {}).get("distribution", {})
                top1 = set(list(dist1.keys())[:10])
                top2 = set(list(dist2.keys())[:10])
                overlap["__".join(sorted([p1, p2]))][str(year)] = round(len(top1 & top2) / 10, 4)

    overlap_trends = {}
    for pair, by_year in overlap.items():
        scores = [by_year[y] for y in sorted(by_year)]
        trend = round(float(scores[-1] - scores[0]), 4) if len(scores) >= 2 else 0
        overlap_trends[pair] = {
            "by_year": by_year, "trend": trend,
            "trend_label": "konvergierend" if trend > 0.1 else "divergierend" if trend < -0.1 else "stabil",
        }

    print(f"  Years with category data: {list(years_data.keys())}")
    print(f"  Overlap pairs: {len(overlap_trends)}")

    return {
        "positive_negative_ratio": pos_neg_by_year,
        "policy_emphasis": emphasis_by_year,
        "programmatic_clarity": clarity_by_year,
        "category_overlap_timeseries": overlap_trends,
    }


# ── 7. Election Results + Correlation ─────────────
def compute_bridging_vote_correlation(bridging_ts: dict, election_results: dict) -> dict:
    """Pearson correlation: bridging score vs. vote share per party."""
    result = {}
    all_ts = {**bridging_ts.get("stable_parties", {}), "afd": bridging_ts.get("afd", {})}

    for pid, year_scores in all_ts.items():
        pairs = [
            (year_scores[y], election_results.get(y, {}).get(pid))
            for y in sorted(year_scores)
            if election_results.get(y, {}).get(pid) is not None
        ]
        if len(pairs) < 3:
            continue
        b, v = np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])
        corr = round(float(np.corrcoef(b, v)[0, 1]), 4)
        result[pid] = {
            "party_name": PARTIES.get(pid, {}).get("name", pid),
            "data_points": [
                {"year": y, "bridging": bs, "vote_share": vs}
                for (y, _), bs, vs in zip(sorted(year_scores.items()), b, v)
            ],
            "pearson_correlation": corr,
            "interpretation": (
                "positiv — zentralere Position korreliert mit mehr Stimmen" if corr > 0.3
                else "negativ — zentralere Position korreliert mit weniger Stimmen" if corr < -0.3
                else "kein klarer Zusammenhang"
            ),
        }
    return result


# ── Main ──────────────────────────────────────────
def run_analysis(skip_llm: bool = False):
    print("Diskursraum — Historical Analysis\n")

    all_years_data, years_found = {}, []
    for year in AVAILABLE_YEARS:
        path = RESULTS_DIR / f"manifestos_{year}.json"
        if path.exists():
            all_years_data[year] = _load_json(path)
            years_found.append(year)
            print(f"Loaded manifestos_{year}.json")
        else:
            print(f"Missing: manifestos_{year}.json")

    if not years_found:
        print("No data — run pipeline first")
        return

    print(f"\nAnalyzing: {years_found}\n")

    print("Step 1: Structural Analysis")
    structural = analyze_structure(years_found)

    print("\nStep 2: Distance Matrices")
    matrices = compute_distance_matrices(all_years_data)

    print("\nStep 3: PCA Trajectories")
    pca = compute_pca_trajectories(years_found)
    if pca:
        print(f"  {len(pca['trajectories'])} parties")

    print("\nStep 4: Election Topics")
    topics = get_election_topics(years_found) if not skip_llm else {}
    if skip_llm:
        print("  Skipped")

    print("\nStep 5: Bridging Time Series")
    bridging_ts = compute_bridging_timeseries(all_years_data)
    print(f"  {list(bridging_ts['stable_parties'].keys())}")

    print("\nStep 6: Category Analysis")
    category_analysis = analyze_categories(years_found)
    if not category_analysis:
        print("  No data — run classify_chunks.py first")

    print("\nStep 7: Election Results + Correlation")
    election_results = _load_json(RESULTS_DIR / "election_results.json").get("results", {})
    correlation = compute_bridging_vote_correlation(bridging_ts, election_results) if election_results else {}
    if correlation:
        print(f"  Computed for: {list(correlation.keys())}")

    output = {
        "years_analyzed": years_found,
        "historical_events": HISTORICAL_EVENTS,
        "structural_analysis": structural,
        "distance_matrices": matrices,
        "pca_trajectories": pca,
        "election_topics": topics,
        "bridging_timeseries": bridging_ts,
        "category_analysis": category_analysis,
        "election_results": election_results,
        "bridging_vote_correlation": correlation,
        "graphs_by_year": {str(y): all_years_data[y].get("graph", {}) for y in years_found},
    }

    path = RESULTS_DIR / "historical_analysis.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: historical_analysis.json ({path.stat().st_size // 1024}KB)")
    print("Done")


if __name__ == "__main__":
    run_analysis(skip_llm="--skip-llm" in sys.argv)