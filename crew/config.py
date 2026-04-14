import os
from dotenv import load_dotenv
from topics import TOPICS

load_dotenv()

# ── Mode ──────────────────────────────────────────
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# ── Bias → Sources Map ────────────────────────────
BIAS_SOURCES = {
    "left":                 ["taz"],
    "left-liberal":         ["spiegel", "zeit", "sz", "stern"],
    "neutral":              ["tagesschau", "zdf", "dw"],
    "conservative-liberal": ["faz", "cicero"],
    "right-conservative":   ["welt", "focus"],
    "far-right":            ["junge_freiheit"],
    "economic-liberal":     ["handelsblatt"],
    "populist-mixed":       ["bild"],
}

SOURCE_BIAS = {
    source_id: bias
    for bias, sources in BIAS_SOURCES.items()
    for source_id in sources
}

BIAS_SPECTRUM = [
    "left",
    "left-liberal",
    "neutral",
    "conservative-liberal",
    "economic-liberal",
    "right-conservative",
    "populist-mixed",
    "far-right",
]

# ── Data Paths ────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
RESULTS_DIR = os.path.join(DATA_DIR, "results")