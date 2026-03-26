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
            model="groq/llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY")
        )

# ── Data Sources ───────────────────────────────────
DATA_SOURCES = ["newsapi", "bluesky", "youtube"]


# ── Data Paths ────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
RESULTS_DIR = os.path.join(DATA_DIR, "results")