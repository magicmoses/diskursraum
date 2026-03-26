import os
from dotenv import load_dotenv
from crewai import LLM

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

# ── Topics ────────────────────────────────────────
TOPICS = {
    "migration": {
        "label": "Migration & Asylum Policy",
        "emoji": "🇩🇪",
        "newsapi_keywords": ["Migration", "Asylpolitik", "Flüchtlinge", "Einwanderung"],
        "bluesky_keywords": ["migration", "asyl", "flüchtlinge"],
        "youtube_channels": ["tagesschau", "SPIEGEL TV", "ZDF"],
        "youtube_keywords": ["migration deutschland", "asylpolitik"]
    },
    "basic_income": {
        "label": "Unconditional Basic Income",
        "emoji": "💰",
        "newsapi_keywords": ["Grundeinkommen", "BGE", "Basic Income"],
        "bluesky_keywords": ["grundeinkommen", "basic income", "bge"],
        "youtube_channels": ["tagesschau", "ZDF", "ARD"],
        "youtube_keywords": ["bedingungsloses grundeinkommen"]
    },
    "nuclear_energy": {
        "label": "Nuclear Energy",
        "emoji": "⚛️",
        "newsapi_keywords": ["Atomkraft", "Kernenergie", "nuclear energy", "AKW"],
        "bluesky_keywords": ["atomkraft", "kernenergie", "nuclear"],
        "youtube_channels": ["tagesschau", "DW News", "ARD"],
        "youtube_keywords": ["atomkraft deutschland", "kernenergie zukunft"]
    },
    "military_service": {
        "label": "Mandatory Military Service",
        "emoji": "🪖",
        "newsapi_keywords": ["Wehrpflicht", "Bundeswehr", "mandatory military"],
        "bluesky_keywords": ["wehrpflicht", "bundeswehr"],
        "youtube_channels": ["tagesschau", "ZDF", "Bundeswehr"],
        "youtube_keywords": ["wehrpflicht wiedereinführung"]
    },
    "retirement_age": {
        "label": "Retirement at 70",
        "emoji": "👴",
        "newsapi_keywords": ["Rente mit 70", "Renteneintrittsalter", "Rentenreform"],
        "bluesky_keywords": ["rente", "rentenalter", "rente mit 70"],
        "youtube_channels": ["tagesschau", "ZDF", "ARD"],
        "youtube_keywords": ["rente mit 70", "rentenreform deutschland"]
    },
    "speed_limit": {
        "label": "Autobahn Speed Limit",
        "emoji": "🚗",
        "newsapi_keywords": ["Tempolimit", "Autobahn", "Geschwindigkeitsbegrenzung"],
        "bluesky_keywords": ["tempolimit", "autobahn"],
        "youtube_channels": ["tagesschau", "ADAC", "ZDF"],
        "youtube_keywords": ["tempolimit autobahn deutschland"]
    },
    "euthanasia": {
        "label": "Assisted Dying",
        "emoji": "💉",
        "newsapi_keywords": ["Sterbehilfe", "Euthanasie", "assisted dying"],
        "bluesky_keywords": ["sterbehilfe", "euthanasie"],
        "youtube_channels": ["tagesschau", "ZDF", "ARD"],
        "youtube_keywords": ["sterbehilfe deutschland debatte"]
    },
    "wealth_tax": {
        "label": "Wealth Tax",
        "emoji": "💸",
        "newsapi_keywords": ["Vermögenssteuer", "Reichensteuer", "wealth tax"],
        "bluesky_keywords": ["vermögenssteuer", "reichensteuer"],
        "youtube_channels": ["tagesschau", "ZDF", "ARD"],
        "youtube_keywords": ["vermögenssteuer deutschland"]
    },
    "ai_jobs": {
        "label": "AI Replacing Jobs",
        "emoji": "🤖",
        "newsapi_keywords": ["KI Arbeitsplätze", "Automatisierung", "AI jobs", "future of work"],
        "bluesky_keywords": ["ai jobs", "automatisierung", "ki arbeit"],
        "youtube_channels": ["Fireship", "tagesschau", "DW News"],
        "youtube_keywords": ["ki ersetzt jobs", "automatisierung arbeitsplätze"]
    },
    "ai_regulation": {
        "label": "AI Regulation & Ethics",
        "emoji": "🧠",
        "newsapi_keywords": ["KI Regulierung", "AI regulation", "AI Act", "KI Ethik"],
        "bluesky_keywords": ["ai regulation", "ki regulierung", "ai act"],
        "youtube_channels": ["tagesschau", "DW News", "Lex Fridman"],
        "youtube_keywords": ["ki regulierung europa", "eu ai act"]
    },
}

# ── Data Paths ────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
RESULTS_DIR = os.path.join(DATA_DIR, "results")