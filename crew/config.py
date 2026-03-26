import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

# ── Mode ──────────────────────────────────────────
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# ── LLM Setup ─────────────────────────────────────
def get_llm() -> LLM:
    """
    Returns the configured LLM based on LLM_PROVIDER env var.
    Defaults to Groq for demo/cloud, Ollama for local dev.
    """
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
        # Default: Groq (free, fast, cloud)
        return LLM(
            model="groq/llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY")
        )

# ── Topics ────────────────────────────────────────
TOPICS = {
    "migration": {
        "label": "Migration & Asylum Policy",
        "emoji": "🇩🇪",
        "source": "reddit",
        "subreddits": ["de", "germany", "europe"],
        "keywords": ["migration", "asyl", "flüchtlinge", "einwanderung"]
    },
    "basic_income": {
        "label": "Unconditional Basic Income",
        "emoji": "💰",
        "source": "reddit",
        "subreddits": ["de", "BasicIncome", "germany"],
        "keywords": ["grundeinkommen", "bge", "basic income"]
    },
    "nuclear_energy": {
        "label": "Nuclear Energy",
        "emoji": "⚛️",
        "source": "both",          # reddit + polis
        "subreddits": ["de", "germany", "energy"],
        "keywords": ["atomkraft", "kernenergie", "nuclear", "akw"]
    },
    "military_service": {
        "label": "Mandatory Military Service",
        "emoji": "🪖",
        "source": "reddit",
        "subreddits": ["de", "germany", "bundeswehr"],
        "keywords": ["wehrpflicht", "bundeswehr", "military service"]
    },
    "retirement_age": {
        "label": "Retirement at 70",
        "emoji": "👴",
        "source": "reddit",
        "subreddits": ["de", "finanzen", "germany"],
        "keywords": ["rente", "renteneintritt", "rente mit 70", "rentenalter"]
    },
    "speed_limit": {
        "label": "Autobahn Speed Limit",
        "emoji": "🚗",
        "source": "reddit",
        "subreddits": ["de", "germany", "autobahn"],
        "keywords": ["tempolimit", "autobahn", "speed limit", "100 kmh"]
    },
    "euthanasia": {
        "label": "Assisted Dying",
        "emoji": "💉",
        "source": "reddit",
        "subreddits": ["de", "germany"],
        "keywords": ["sterbehilfe", "euthanasie", "assisted dying"]
    },
    "wealth_tax": {
        "label": "Wealth Tax",
        "emoji": "💸",
        "source": "reddit",
        "subreddits": ["de", "wirtschaft", "finanzen"],
        "keywords": ["vermögenssteuer", "reichensteuer", "wealth tax"]
    },
    "ai_jobs": {
        "label": "AI Replacing Jobs",
        "emoji": "🤖",
        "source": "reddit",
        "subreddits": ["Futurology", "de", "artificial", "ChatGPT"],
        "keywords": ["ai jobs", "automatisierung", "ki ersetzt", "future of work"]
    },
    "ai_regulation": {
        "label": "AI Regulation & Ethics",
        "emoji": "🧠",
        "source": "polis",         # Taiwan dataset only
        "subreddits": [],
        "keywords": []
    },
}

# ── Data Paths ────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
REDDIT_CACHE_DIR = os.path.join(DATA_DIR, "reddit")
POLIS_DIR = os.path.join(DATA_DIR, "polis")
RESULTS_DIR = os.path.join(DATA_DIR, "results")