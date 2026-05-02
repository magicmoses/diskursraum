"""
classify_chunks.py — ManifestoBERTa Chunk Classification

Classifies all chunks in ChromaDB using ManifestoBERTa
(manifesto-project/manifestoberta-xlm-roberta-56policy-topics-context-2024-1-1)

Each chunk gets assigned one of 56 political policy categories
from the Manifesto Project coding scheme.

Pipeline:
  1. Load chunks from ChromaDB per year
  2. Classify each chunk with ManifestoBERTa
  3. Store category labels back in ChromaDB metadata
  4. Export category_distribution_{year}.json

Output per year:
  - Category distribution per party
  - Top categories per party
  - Category overlap between parties
  - Category shift over time (when run for multiple years)

Run:
  python classify_chunks.py 2025
  python classify_chunks.py --all   # all available years
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent))

BASE_DIR = Path(__file__).parent.parent.parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
RESULTS_DIR = BASE_DIR / "data" / "results"

MODEL_NAME = "manifesto-project/manifestoberta-xlm-roberta-56policy-topics-context-2024-1-1"

PARTIES = {
    "cdu_csu": "CDU/CSU",
    "spd":     "SPD",
    "gruene":  "Bündnis 90/Die Grünen",
    "fdp":     "FDP",
    "afd":     "AfD",
    "linke":   "Die Linke",
}

# Map 56 categories to broader readable labels
# Full codebook: https://manifesto-project.wzb.eu/information/documents/handbook
CATEGORY_GROUPS = {
    "external_relations": [101, 102, 103, 104, 105, 106, 107, 108],
    "freedom_democracy":  [201, 202, 203, 204],
    "political_system":   [301, 302, 303, 304, 305],
    "economy":            [401, 402, 403, 404, 405, 406, 407, 408, 409, 410],
    "welfare":            [501, 502, 503, 504, 505, 506, 507],
    "fabric_of_society":  [601, 602, 603, 604, 605, 606, 607, 608],
    "social_groups":      [701, 702, 703, 704],
}


def load_manifestoberta():
    """Loads ManifestoBERTa classification model and tokenizer."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import torch

    print(f"Loading ManifestoBERTa (~2.24GB, first run will download)...")
    print(f"Model: {MODEL_NAME}")

    tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-large")
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )
    model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    print(f"Model loaded on {device}")

    return model, tokenizer, device


def classify_chunk(text: str, model, tokenizer, device, context: str = None) -> tuple[str, float]:
    """
    Classifies a single chunk using ManifestoBERTa.
    Uses context (surrounding text) if available for better accuracy.
    Returns (category_label, confidence_score).
    """
    import torch

    # Context model expects: sentence + surrounding context
    if context is None:
        context = text

    inputs = tokenizer(
        text,
        context,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True,
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        top_prob, top_idx = probs.max(dim=-1)

    # Get label from model config
    label = model.config.id2label[top_idx.item()]
    confidence = round(top_prob.item(), 4)

    return label, confidence


def classify_party_chunks(
    party_id: str,
    year: int,
    model,
    tokenizer,
    device,
) -> list[dict]:
    """
    Retrieves all chunks for a party+year from ChromaDB
    and classifies each with ManifestoBERTa.
    """
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        collection = client.get_collection(f"manifestos_{year}")
    except Exception:
        print(f"  Collection manifestos_{year} not found")
        return []

    results = collection.get(
        where={"party_id": party_id},
        include=["documents", "metadatas"],
    )

    if not results["documents"]:
        return []

    chunks = results["documents"]
    print(f"  Classifying {len(chunks)} chunks for {PARTIES.get(party_id, party_id)}...")

    classified = []
    for i, chunk in enumerate(chunks):
        # Use adjacent chunk as context if available
        context = chunks[i-1] if i > 0 else chunk
        label, confidence = classify_chunk(chunk, model, tokenizer, device, context)

        classified.append({
            "chunk_index": i,
            "text": chunk[:200],  # truncate for storage
            "category": label,
            "confidence": confidence,
        })

        if (i + 1) % 20 == 0:
            print(f"    {i+1}/{len(chunks)} classified", flush=True)

    return classified


def compute_category_distribution(classified_chunks: list[dict]) -> dict:
    """
    Computes category distribution from classified chunks.
    Returns counts, percentages, and top categories.
    """
    category_counts = Counter(c["category"] for c in classified_chunks)
    total = len(classified_chunks)

    distribution = {
        cat: {
            "count": count,
            "pct": round(count * 100 / total, 2),
        }
        for cat, count in category_counts.most_common()
    }

    # Group into broader categories
    group_counts = defaultdict(int)
    for cat, count in category_counts.items():
        try:
            cat_code = int(cat.split("_")[0]) if "_" in cat else int(cat)
            for group, codes in CATEGORY_GROUPS.items():
                if cat_code in codes:
                    group_counts[group] += count
                    break
            else:
                group_counts["other"] += count
        except (ValueError, AttributeError):
            group_counts["other"] += count

    return {
        "total_chunks": total,
        "distribution": distribution,
        "top_5": list(distribution.keys())[:5],
        "group_distribution": {
            group: {
                "count": count,
                "pct": round(count * 100 / total, 2),
            }
            for group, count in sorted(group_counts.items(), key=lambda x: x[1], reverse=True)
        },
    }


def compute_category_overlap(party_distributions: dict) -> dict:
    """
    Computes category overlap between parties.
    Higher overlap = parties focus on similar policy areas.
    """
    overlap = {}

    party_ids = list(party_distributions.keys())
    for i, p1 in enumerate(party_ids):
        for p2 in party_ids[i+1:]:
            dist1 = party_distributions[p1]["distribution"]
            dist2 = party_distributions[p2]["distribution"]

            # All categories across both parties
            all_cats = set(dist1.keys()) | set(dist2.keys())
            total = len(all_cats)

            if total == 0:
                continue

            # Shared top-10 categories
            top1 = set(list(dist1.keys())[:10])
            top2 = set(list(dist2.keys())[:10])
            shared = top1 & top2

            key = "__".join(sorted([p1, p2]))
            overlap[key] = {
                "shared_top_categories": list(shared),
                "overlap_score": round(len(shared) / 10, 4),
            }

    return overlap


def run_classification(year: int):
    """Full classification pipeline for one year."""
    print(f"\nManifestoBERTa Classification — {year}")

    model, tokenizer, device = load_manifestoberta()

    party_results = {}

    for party_id in PARTIES.keys():
        print(f"\n  [{PARTIES[party_id]}]")
        classified = classify_party_chunks(party_id, year, model, tokenizer, device)

        if not classified:
            print(f"  No chunks found — skipping")
            continue

        distribution = compute_category_distribution(classified)
        party_results[party_id] = {
            "party_id": party_id,
            "party_name": PARTIES[party_id],
            "year": year,
            "classified_chunks": classified,
            "distribution": distribution,
        }
        print(f"  Top categories: {distribution['top_5']}")

    if not party_results:
        print("No results — aborting")
        return

    # Category overlap between parties
    print("\nComputing category overlap...")
    party_distributions = {
        pid: data["distribution"]
        for pid, data in party_results.items()
    }
    overlap = compute_category_overlap(party_distributions)

    output = {
        "year": year,
        "model": MODEL_NAME,
        "parties": party_results,
        "category_overlap": overlap,
    }

    # Export — strip full chunk text to reduce file size
    output_slim = {
        "year": year,
        "model": MODEL_NAME,
        "parties": {
            pid: {
                "party_id": data["party_id"],
                "party_name": data["party_name"],
                "year": data["year"],
                "distribution": data["distribution"],
            }
            for pid, data in party_results.items()
        },
        "category_overlap": overlap,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"category_distribution_{year}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_slim, f, ensure_ascii=False, indent=2)

    size_kb = output_path.stat().st_size // 1024
    print(f"\nSaved: category_distribution_{year}.json ({size_kb}KB)")
    print("Classification complete")


if __name__ == "__main__":
    years_available = [2005, 2009, 2013, 2017, 2021, 2025]

    if "--all" in sys.argv:
        for year in years_available:
            run_classification(year)
    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        run_classification(int(sys.argv[1]))
    else:
        print("Usage:")
        print("  python classify_chunks.py 2025")
        print("  python classify_chunks.py --all")