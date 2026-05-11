"""
popbert_scorer.py — Populismus-Score für Wahlprogramme 2005-2025

Modell: przvl/PopEuroBERT-binary-610m
Basis:  EuroBERT-610M, finetuned auf PopBERT-Datensatz (Erhard et al. 2025)
Task:   Binäre Klassifikation: populistisch / neutral

Output pro Partei/Jahr:
  populism_score — Anteil Sätze mit populist_prob > 0.43
  sentence_count — Anzahl analysierter Sätze
  chunk_count    — Anzahl ChromaDB-Chunks

Output: data/results/manifesto_hohenheim.json
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

BASE_DIR   = Path(__file__).parent.parent.parent.parent
CHROMA_DIR = str(BASE_DIR / "data" / "chroma_db")
OUTPUT     = BASE_DIR / "data" / "results" / "manifesto_hohenheim.json"

MODEL_ID  = "przvl/PopEuroBERT-binary-610m"
THRESHOLD = 0.43
MAX_LEN   = 256
BATCH     = 32

PARTIES   = ["cdu_csu", "spd", "gruene", "fdp", "afd", "linke"]
YEARS     = [2005, 2009, 2013, 2017, 2021, 2025]
AFD_SINCE = 2013


# ── Sentence splitting ────────────────────────────
def split_sentences(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in parts if len(s.strip()) > 15]


# ── ChromaDB chunk loading ────────────────────────
def load_chunks(year: int, party_id: str) -> list[str]:
    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        collection = client.get_collection(f"manifestos_{year}")
        results = collection.get(
            where={"party_id": party_id},
            include=["documents"],
        )
        return results["documents"] or []
    except Exception as e:
        print(f"    ChromaDB error ({party_id} {year}): {e}")
        return []


# ── Batch inference ───────────────────────────────
def score_sentences(tokenizer, model, sentences: list[str]) -> tuple[float, int]:
    """Returns (populism_score, n_sentences).
    populism_score = fraction of sentences with prob > THRESHOLD
    """
    all_probs = []

    for i in range(0, len(sentences), BATCH):
        batch = sentences[i : i + BATCH]
        enc = tokenizer(
            batch,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_LEN,
            padding=True,
        )
        with torch.no_grad():
            logits = model(**enc).logits
        probs = torch.softmax(logits, dim=-1)[:, 1].tolist()
        all_probs.extend(probs)

    if not all_probs:
        return 0.0, 0

    n = len(all_probs)
    return round(sum(p > THRESHOLD for p in all_probs) / n, 3), n


# ── Main ──────────────────────────────────────────
def run():
    print(f"Loading {MODEL_ID}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_ID, trust_remote_code=True
        )
        model.eval()
        print("  Model ready.\n")
    except Exception as e:
        print(f"\nERROR: Could not load model: {e}")
        return

    # Load or create output JSON — only overwrite populism fields
    if OUTPUT.exists():
        with open(OUTPUT, "r", encoding="utf-8") as f:
            output = json.load(f)
    else:
        output = {}

    output["description"] = "Populismus-Scores nach PopEuroBERT (Erhard et al. 2025)"
    output["model"]       = MODEL_ID
    output["threshold"]   = THRESHOLD
    output["computed_at"] = datetime.utcnow().isoformat()
    if "scores" not in output:
        output["scores"] = {}

    # ── Per year / per party ──────────────────────
    for year in YEARS:
        key = str(year)
        if key not in output["scores"]:
            output["scores"][key] = {}

        print(f"── {year} ─────────────────────────")

        for party_id in PARTIES:
            if party_id == "afd" and year < AFD_SINCE:
                output["scores"][key][party_id] = {
                    "populism_score": None,
                    "sentence_count": 0,
                    "chunk_count":    0,
                    "note":           "not_in_bundestag",
                }
                continue

            print(f"  {party_id}...", end=" ", flush=True)

            chunks = load_chunks(year, party_id)
            if not chunks:
                print("no chunks — skipped")
                output["scores"][key][party_id] = {
                    "populism_score": None,
                    "sentence_count": 0,
                    "chunk_count":    0,
                    "note":           "no_data",
                }
                continue

            sentences = []
            for chunk in chunks:
                sentences.extend(split_sentences(chunk))

            if not sentences:
                print("no sentences — skipped")
                output["scores"][key][party_id] = {
                    "populism_score": None,
                    "sentence_count": 0,
                    "chunk_count":    len(chunks),
                }
                continue

            p_score, n = score_sentences(tokenizer, model, sentences)

            # Preserve existing non-populism fields, overwrite populism fields
            entry = output["scores"][key].get(party_id, {})
            entry.update({
                "populism_score": p_score,
                "sentence_count": n,
                "chunk_count":    len(chunks),
            })
            output["scores"][key][party_id] = entry

            print(f"score={p_score}  ({n} sentences)")

        # Save after each year — crash-safe
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"  → Saved {year}\n")

    # ── Plausibility check ────────────────────────
    print("═" * 50)
    print("Plausibility Check (2025 — populism_score)")
    print("═" * 50)

    s25 = output["scores"].get("2025", {})

    def score(p):
        return s25.get(p, {}).get("populism_score")

    ranking = sorted(
        [(p, score(p)) for p in PARTIES if score(p) is not None],
        key=lambda x: x[1], reverse=True,
    )
    for party, val in ranking:
        bar = "█" * int(val * 50)
        print(f"  {party:<12} {val:.3f}  {bar}")

    afd_s = score("afd")
    cdu_s = score("cdu_csu")
    lin_s = score("linke")
    fdp_s = score("fdp")

    checks = [
        ("AfD > CDU (anti-elitism proxy)",     afd_s and cdu_s and afd_s > cdu_s),
        ("Linke > FDP (left-populism proxy)",  lin_s and fdp_s and lin_s > fdp_s),
        ("CDU populism_score < 0.15",          cdu_s is not None and cdu_s < 0.15),
    ]
    print()
    for label, passed in checks:
        print(f"  {'✓' if passed else '✗'}  {label}")

    print(f"\n✅ Done — {OUTPUT}")


if __name__ == "__main__":
    run()
