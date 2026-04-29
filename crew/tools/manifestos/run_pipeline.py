"""
run_pipeline.py — Orchestrates the full manifesto analysis pipeline.

Usage:
  python run_pipeline.py              # processes 2025
  python run_pipeline.py 2021         # processes specific year
  python run_pipeline.py 2025 --skip-pdf  # skip PDF processing, use existing ChromaDB
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

BASE_DIR = Path(__file__).parent.parent.parent.parent
MANIFESTOS_DIR = BASE_DIR / "data" / "manifestos"
RESULTS_DIR = BASE_DIR / "data" / "results"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

PARTIES = {
    "cdu_csu": {"name": "CDU/CSU",              "bias": "conservative-liberal", "color": "#000000"},
    "spd":     {"name": "SPD",                   "bias": "left-liberal",         "color": "#E3000F"},
    "gruene":  {"name": "Bündnis 90/Die Grünen", "bias": "left-liberal",         "color": "#1AA037"},
    "fdp":     {"name": "FDP",                   "bias": "economic-liberal",     "color": "#FFED00"},
    "afd":     {"name": "AfD",                   "bias": "far-right",            "color": "#009EE0"},
    "linke":   {"name": "Die Linke",             "bias": "left",                 "color": "#BE3075"},
}

TOPIC_KEYWORDS = {
    "migration":         ["migration", "asyl", "flüchtlinge", "einwanderung", "abschiebung", "integration", "zuwanderung", "grenzschutz"],
    "energy_transition": ["energiewende", "erneuerbare energien", "atomkraft", "kernenergie", "windenergie", "solarenergie", "kohleausstieg", "klimaschutz"],
    "retirement":        ["rente", "rentenpolitik", "rentenreform", "altersvorsorge", "rentenalter", "rentenniveau", "altersarmut"],
    "wealth_tax":        ["vermögenssteuer", "erbschaftssteuer", "umverteilung", "steuergerechtigkeit", "reichensteuer", "spitzensteuersatz"],
    "digitalization":    ["digitalisierung", "künstliche intelligenz", "ki", "digitale transformation", "datenschutz", "cybersicherheit"],
}

TOPIC_LABELS = {
    "migration":         "Migration & Asylpolitik",
    "energy_transition": "Energiewende",
    "retirement":        "Rente & Altersvorsorge",
    "wealth_tax":        "Vermögenssteuer & Umverteilung",
    "digitalization":    "Digitale Transformation & KI",
}

# Test mode — reduce scope for quick iteration
PARTIES_TEST = {"cdu_csu": PARTIES["cdu_csu"]}
TOPICS_TEST = {"migration": TOPIC_KEYWORDS["migration"]}


def run_pipeline(year: int = 2025, skip_pdf: bool = False, test_mode: bool = False):
    from pdf_processor import process_party_pdf, load_embedding_model
    from graph_builder import get_party_topic_embeddings, compute_bridging_scores, build_party_graph
    from manifesto_analyzer import analyze_topic_full
    from manifesto_exporter import export_results

    parties = PARTIES_TEST if test_mode else PARTIES
    topic_keywords = TOPICS_TEST if test_mode else TOPIC_KEYWORDS

    print(f"Diskursraum — Manifesto Pipeline {year}")
    print(f"LLM Provider: {os.getenv('LLM_PROVIDER', 'groq').upper()}")
    print(f"Parties: {list(parties.keys())}")
    print(f"Topics: {list(topic_keywords.keys())}\n")

    model = load_embedding_model()

    # Phase 1: PDF Processing
    processed_parties = []

    if not skip_pdf:
        print("Phase 1: Processing PDFs")
        manifesto_dir = MANIFESTOS_DIR / str(year)

        if not manifesto_dir.exists():
            print(f"Directory not found: {manifesto_dir}")
            return

        for party_id, party_info in parties.items():
            chunks = process_party_pdf(
                party_id=party_id,
                party_info=party_info,
                year=year,
                manifesto_dir=manifesto_dir,
                chroma_dir=CHROMA_DIR,
                model=model,
            )
            if chunks is not None:
                processed_parties.append(party_id)

        print(f"\nPhase 1 complete: {len(processed_parties)} parties processed")
    else:
        print("Phase 1: Skipping PDF processing (--skip-pdf)")
        processed_parties = list(parties.keys())

    if not processed_parties:
        print("No parties processed — aborting")
        return

    # Phase 2: Topic Analysis + Bridging Scores
    print("\nPhase 2: Topic Analysis + Bridging Scores")
    all_topic_results = {}

    for topic_id, keywords in topic_keywords.items():
        topic_label = TOPIC_LABELS[topic_id]
        print(f"\n  {topic_label}")

        topic_party_data = {}
        topic_party_embeddings = {}

        for party_id in processed_parties:
            chunks, embeddings, distances = get_party_topic_embeddings(
                party_id=party_id,
                topic_id=topic_id,
                topic_keywords=keywords,
                topic_label=topic_label,
                party_name=parties[party_id]["name"],
                year=year,
                chroma_dir=CHROMA_DIR,
                model=model,
            )

            if chunks is None:
                continue

            topic_party_data[party_id] = {
                "party_id": party_id,
                "party_name": parties[party_id]["name"],
                "bias": parties[party_id]["bias"],
                "top_chunks": chunks,
                "relevance_scores": [round(1 - d, 4) for d in distances],
            }
            topic_party_embeddings[party_id] = embeddings
            print(f"    {parties[party_id]['name']}: {len(chunks)} chunks retrieved")

        if len(topic_party_embeddings) < 2:
            print(f"    Not enough parties for bridging — skipping")
            continue

        bridging = compute_bridging_scores(topic_id, topic_party_embeddings, parties)
        print(f"    Most bridging: {bridging['most_bridging_party_name']} "
              f"(score: {bridging['bridging_scores'].get(bridging['most_bridging_party'], 0):.4f})")

        all_topic_results[topic_id] = {
            "topic_id": topic_id,
            "topic_label": topic_label,
            "parties": topic_party_data,
            "bridging": bridging,
        }

    # Phase 3: LLM Analysis
    print("\nPhase 3: LLM Analysis")
    for topic_id, topic_data in all_topic_results.items():
        print(f"\n  {TOPIC_LABELS[topic_id]}")
        analyzed = analyze_topic_full(
            topic_id=topic_id,
            topic_label=TOPIC_LABELS[topic_id],
            topic_party_data=topic_data["parties"],
            bridging_data=topic_data["bridging"],
            parties=parties,
        )
        all_topic_results[topic_id] = analyzed

    # Phase 4: Build Graph
    print("\nPhase 4: Building graph")
    graph = build_party_graph(
        all_topic_results=all_topic_results,
        parties=parties,
        output_dir=RESULTS_DIR,
    )
    print(f"  {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    print(f"  Most bridging party: {graph.get('most_bridging_party_name')}")
    print(f"  Topic subgraphs: {list(graph.get('topic_subgraphs', {}).keys())}")

    # Phase 5: Export
    print("\nPhase 5: Exporting JSON")
    export_results(
        year=year,
        parties=parties,
        topics=list(topic_keywords.keys()),
        all_topic_results=all_topic_results,
        graph=graph,
        results_dir=RESULTS_DIR,
    )

    print("\nPipeline complete")


if __name__ == "__main__":
    year = 2025
    skip_pdf = False
    test_mode = False

    for arg in sys.argv[1:]:
        if arg.isdigit():
            year = int(arg)
        elif arg == "--skip-pdf":
            skip_pdf = True
        elif arg == "--test":
            test_mode = True

    run_pipeline(year=year, skip_pdf=skip_pdf, test_mode=test_mode)