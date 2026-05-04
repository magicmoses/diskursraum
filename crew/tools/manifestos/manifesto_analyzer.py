"""
manifesto_analyzer.py — LLM-based Analysis per Topic

Uses ChromaDB results + LLM to generate:
  - Per-party position summary on a topic
  - Cross-party shared perspectives
  - Cross-party controversial points
  - Most bridging party explanation

Analog to bridging_scorer.py for news articles.
Uses call_llm() from bridging_scorer.py for Groq/Ollama.
"""

import os
import sys
import json
import re
import numpy as np
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


def call_llm(prompt: str, max_tokens: int = 400) -> str:
    """Groq first, Anthropic fallback on rate limit."""

    def _groq():
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    def _anthropic():
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    # Explizit Anthropic gewählt
    if os.getenv("LLM_PROVIDER", "groq").lower() == "anthropic":
        return _anthropic()

    # Groq first, Anthropic fallback bei Rate Limit
    try:
        return _groq()
    except Exception as e:
        if "429" in str(e) or "rate_limit" in str(e).lower():
            print(f"    Groq rate limit — falling back to Anthropic")
            return _anthropic()
        raise

def summarize_party_position(
    party_name: str,
    topic_label: str,
    chunks: list[str],
) -> str:
    """
    Generates a 2-3 sentence summary of a party's position on a topic.
    Based on the top relevant chunks from the manifesto.
    """
    chunks_text = "\n\n".join([f"[{i+1}] {c}" for i, c in enumerate(chunks[:3])])

    prompt = f"""Du analysierst das Wahlprogramm der Partei {party_name}.

Hier sind die relevantesten Passagen zum Thema "{topic_label}":

{chunks_text}

Fasse in 2-3 Sätzen auf Deutsch zusammen, wie sich {party_name} zu diesem Thema positioniert.
Sei präzise und beziehe dich auf konkrete Aussagen aus den Texten."""

    try:
        return call_llm(prompt, max_tokens=200)
    except Exception as e:
        print(f"  ⚠ Summary failed for {party_name}: {e}")
        return "Zusammenfassung nicht verfügbar."


def synthesize_cross_party(
    topic_label: str,
    party_positions: dict[str, str],
) -> dict:
    """
    Generates cross-party synthesis:
    - What do all parties agree on?
    - Where do they diverge most?
    - Which party has the most bridging position?
    """
    positions_text = "\n\n".join([
        f"{party}: {summary}"
        for party, summary in party_positions.items()
    ])

    prompt = f"""Du analysierst die Positionen deutscher Parteien zum Thema "{topic_label}".

Hier sind die Positionen der Parteien:

{positions_text}

Antworte auf Deutsch im JSON-Format:
{{
  "shared": "1-2 Sätze: Was haben alle Parteien gemeinsam?",
  "controversial": "1-2 Sätze: Wo divergieren die Positionen am stärksten?",
  "spectrum": "1 Satz: Wie sieht das Links-Rechts-Spektrum bei diesem Thema aus?"
}}"""

    try:
        raw = call_llm(prompt, max_tokens=400)
        raw = re.sub(r'```json|```', '', raw).strip()
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            return {
                "shared_perspectives": result.get("shared", ""),
                "controversial_points": result.get("controversial", ""),
                "spectrum_description": result.get("spectrum", ""),
            }
    except Exception as e:
        print(f"  Synthesis failed: {e}")

    return {
        "shared_perspectives": "Synthese nicht verfügbar.",
        "controversial_points": "Synthese nicht verfügbar.",
        "spectrum_description": "",
    }


def analyze_topic_full(
    topic_id: str,
    topic_label: str,
    topic_party_data: dict,
    bridging_data: dict,
    parties: dict,
) -> dict:
    """
    Full analysis for one topic:
    1. Per-party position summary
    2. Cross-party synthesis
    3. Combine with bridging scores

    Returns structured result for JSON export.
    """
    print(f" Generating party summaries...")
    party_summaries = {}

    for party_id, data in topic_party_data.items():
        party_name = parties[party_id]["name"]
        chunks = data.get("top_chunks", [])
        if chunks:
            summary = summarize_party_position(
                party_name=party_name,
                topic_label=topic_label,
                chunks=chunks,
            )
            party_summaries[party_name] = summary
            data["position_summary"] = summary

    print(f" Generating cross-party synthesis...")
    synthesis = synthesize_cross_party(topic_label, party_summaries)

    return {
        "topic_id": topic_id,
        "topic_label": topic_label,
        "parties": topic_party_data,
        "bridging": bridging_data,
        "synthesis": synthesis,
    }