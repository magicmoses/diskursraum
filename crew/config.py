import os
from dotenv import load_dotenv
from crewai import LLM
from topics import TOPICS

load_dotenv()

# ── Mode ──────────────────────────────────────────
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()


# ── LLM Setup ─────────────────────────────────────
def get_llm() -> LLM:
    if LLM_PROVIDER == "ollama":
        return LLM(
            model="ollama/llama3.1",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
    elif LLM_PROVIDER == "openai":
        return LLM(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
    else:
        # Default: Groq
        return LLM(
            model="groq/llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY")
        )


# ── Bias → Sources Map ────────────────────────────
# Explicit mapping of bias groups to their source_ids.
# Used for two-level bridging score calculation:
#   Level 1: Bias-group bridging (main signal, 70%)
#   Level 2: Source-level bridging within bias group (30%)
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

# Reverse map: source_id → bias group
SOURCE_BIAS = {
    source_id: bias
    for bias, sources in BIAS_SOURCES.items()
    for source_id in sources
}

# Ordered bias spectrum (left to right)
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


# ── Data Sources ──────────────────────────────────
DATA_SOURCES = ["newsapi", "bluesky", "youtube"]


# ── Data Paths ────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
RESULTS_DIR = os.path.join(DATA_DIR, "results")