"""
manifesto_exporter.py — JSON Export for Static Deployment

Exports manifesto analysis results as JSON files.
Committed to repo → served statically by Railway.

Output: data/results/manifestos_{year}.json
"""

import json
from datetime import datetime
from pathlib import Path


def export_results(
    year: int,
    parties: dict,
    topics: list[str],
    all_topic_results: dict,
    graph: dict,
    results_dir: Path,
) -> Path:
    """
    Exports complete analysis as JSON.
    Strips large fields (raw chunks) for smaller file size.
    """
    results_dir.mkdir(parents=True, exist_ok=True)

    # Slim down output — keep top 3 chunks per party per topic
    slim_results = {}
    for topic_id, topic_data in all_topic_results.items():
        slim_parties = {}
        for party_id, party_data in topic_data.get("parties", {}).items():
            slim_parties[party_id] = {
                "party_id": party_data["party_id"],
                "party_name": party_data["party_name"],
                "bias": party_data["bias"],
                "top_chunks": party_data.get("top_chunks", [])[:3],
                "relevance_scores": party_data.get("relevance_scores", [])[:3],
                "position_summary": party_data.get("position_summary", ""),
            }

        slim_results[topic_id] = {
            "topic_id": topic_id,
            "topic_label": topic_data.get("topic_label", topic_id),
            "parties": slim_parties,
            "bridging": topic_data.get("bridging", {}),
            "synthesis": topic_data.get("synthesis", {}),
        }

    output = {
        "computed_at": datetime.utcnow().isoformat(),
        "year": year,
        "parties": parties,
        "topics": topics,
        "results": slim_results,
        "graph": graph,
    }

    output_path = results_dir / f"manifestos_{year}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    size_kb = output_path.stat().st_size // 1024
    print(f"  Saved: manifestos_{year}.json ({size_kb}KB)")

    return output_path