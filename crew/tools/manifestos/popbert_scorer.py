# TODO (phase 2): Still reads chunks from ChromaDB (data/chroma_db/ — gitignored,
# built locally, not reproducible from a clean clone). The production API (api/frag_nach.py)
# has already been migrated to pgvector (manifesto_chunks table). This script should
# query pgvector instead. Low priority — runs manually, once per election cycle (~4 yrs).

"""
popbert_scorer.py — Populismus-Score für Wahlprogramme 2005-2025

Modell: przvl/PopEuroBERT-binary-610m
Basis:  EuroBERT-610M, finetuned auf PopBERT-Datensatz (Erhard et al. 2025)
Task:   Binäre Klassifikation: populistisch / neutral

Output pro Partei/Jahr:
  populism_score — Anteil Sätze mit populist_prob > 0.43
  sentence_count — Anzpythahl analysierter Sätze
  chunk_count    — Anzahl ChromaDB-Chunks

Output: data/results/manifesto_hohenheim.json

Usage:
  python popbert_scorer.py              # alle Jahre
  python popbert_scorer.py 2017 2021    # nur diese Jahre
  python popbert_scorer.py --force 2017 # bereits berechnete überschreiben
"""

import re
import sys
import json
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoConfig, AutoModelForSequenceClassification
from safetensors.torch import load_file
from huggingface_hub import hf_hub_download

BASE_DIR   = Path(__file__).parent.parent.parent.parent
CHROMA_DIR = str(BASE_DIR / "data" / "chroma_db")
OUTPUT     = BASE_DIR / "data" / "results" / "manifesto_hohenheim.json"

MODEL_ID   = "przvl/PopEuroBERT-binary-610m"
THRESHOLD  = 0.43
MAX_LEN    = 256
BATCH      = 32

ALL_YEARS  = [2005, 2009, 2013, 2017, 2021, 2025]
PARTIES    = ["cdu_csu", "spd", "gruene", "fdp", "afd", "linke"]
AFD_SINCE  = 2013


# ── CLI args ──────────────────────────────────────
def parse_args() -> tuple[list[int], bool]:
    """
    Returns (years_to_run, force).
    Examples:
      popbert_scorer.py              → alle Jahre, kein force
      popbert_scorer.py 2017 2021    → nur 2017+2021, kein force
      popbert_scorer.py --force      → alle Jahre, force
      popbert_scorer.py --force 2017 → nur 2017, force
    """
    args = sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]

    if args:
        try:
            years = [int(a) for a in args]
            invalid = [y for y in years if y not in ALL_YEARS]
            if invalid:
                print(f"ERROR: Ungültige Jahre: {invalid}")
                print(f"Verfügbar: {ALL_YEARS}")
                sys.exit(1)
        except ValueError:
            print(f"ERROR: Ungültige Argumente: {args}")
            print("Usage: python popbert_scorer.py [--force] [YEAR ...]")
            sys.exit(1)
    else:
        years = ALL_YEARS

    return years, force


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


# ── Merge score into years structure ─────────────
def merge_score(output: dict, year_key: str, party_id: str, pop_score: float):
    party_entry = output.get("years", {}).get(year_key, {}).get(party_id)
    if isinstance(party_entry, dict):
        party_entry["populism"] = {
            "anti_elitism": pop_score,
            "left_populism": None,
            "right_populism": None,
        }


# ── Save ─────────────────────────────────────────
def save(output: dict):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


# ── Main ──────────────────────────────────────────
def run():
    years, force = parse_args()

    print(f"Jahre: {years}  |  Force: {force}")
    print(f"Loading {MODEL_ID}...")

    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

        config = AutoConfig.from_pretrained(MODEL_ID)
        model = AutoModelForSequenceClassification.from_config(config)

        weights_path = hf_hub_download(MODEL_ID, "model.safetensors")
        raw = load_file(weights_path)

        remapped = {}
        for k, v in raw.items():
            if k.startswith("inner_model.model."):
                remapped[k[len("inner_model."):]] = v
            elif k.startswith("inner_model.dense."):
                remapped[k[len("inner_model."):]] = v
            elif k.startswith("inner_model.out_proj."):
                remapped["classifier." + k[len("inner_model.out_proj."):]] = v
            else:
                remapped[k] = v

        missing, _ = model.load_state_dict(remapped, strict=False)
        if missing:
            print(f"  WARNING: {len(missing)} keys still missing after remap")

        model.eval()
        print("  Model ready.\n")
    except Exception as e:
        print(f"\nERROR: Could not load model: {e}")
        return

    if OUTPUT.exists():
        with open(OUTPUT, "r", encoding="utf-8") as f:
            output = json.load(f)
    else:
        output = {}

    output["computed_at"] = datetime.utcnow().isoformat()
    if "scores" not in output:
        output["scores"] = {}

    # ── Per year / per party ──────────────────────
    for year in years:
        key = str(year)
        if key not in output["scores"]:
            output["scores"][key] = {}

        print(f"── {year} ─────────────────────────")

        for party_id in PARTIES:
            if party_id == "afd" and year < AFD_SINCE:
                continue

            # Skip bereits berechnete Werte — außer bei --force
            existing_score = (
                output.get("years", {})
                .get(key, {})
                .get(party_id, {})
                .get("populism", {})
                .get("anti_elitism")
            )
            if existing_score is not None and not force:
                print(f"  {party_id}... bereits berechnet ({existing_score}) — skip")
                continue

            print(f"  {party_id}...", end=" ", flush=True)

            chunks = load_chunks(year, party_id)
            if not chunks:
                print("no chunks — skipped")
                continue

            sentences = []
            for chunk in chunks:
                sentences.extend(split_sentences(chunk))

            if not sentences:
                print("no sentences — skipped")
                continue

            p_score, n = score_sentences(tokenizer, model, sentences)

            entry = output["scores"][key].get(party_id, {})
            entry.update({
                "populism_score": p_score,
                "sentence_count": n,
                "chunk_count":    len(chunks),
            })
            output["scores"][key][party_id] = entry

            merge_score(output, key, party_id, p_score)

            print(f"score={p_score}  ({n} sentences)")

            # Nach jeder Partei speichern — crash-safe
            save(output)
            print(f"    → saved {party_id} {year}")

        print(f"  → Year {year} complete\n")

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
        ("AfD > CDU (anti-elitism proxy)",    afd_s and cdu_s and afd_s > cdu_s),
        ("Linke > FDP (left-populism proxy)", lin_s and fdp_s and lin_s > fdp_s),
        ("CDU populism_score < 0.15",         cdu_s is not None and cdu_s < 0.15),
    ]
    print()
    for label, passed in checks:
        print(f"  {'✓' if passed else '✗'}  {label}")

    print(f"\n Done — {OUTPUT}")


if __name__ == "__main__":
    run()