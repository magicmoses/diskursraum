# ── Topics ────────────────────────────────────────
# Separated from config.py so crawler can import
# without requiring crewai or other heavy dependencies

TOPICS = {
    "migration": {
        "label": "Migration & Asylum Policy",
        "emoji": "🇩🇪",
        "newsapi_keywords": ["Migration", "Asylpolitik", "Flüchtlinge", "Einwanderung", "Asyl"]
    },
    "basic_income": {
        "label": "Unconditional Basic Income",
        "emoji": "💰",
        "newsapi_keywords": ["Grundeinkommen", "BGE", "Basic Income", "bedingungsloses Grundeinkommen"]
    },
    "nuclear_energy": {
        "label": "Nuclear Energy",
        "emoji": "⚛️",
        "newsapi_keywords": ["Atomkraft", "Kernenergie", "nuclear energy", "AKW", "Kernkraft"]
    },
    "military_service": {
        "label": "Mandatory Military Service",
        "emoji": "🪖",
        "newsapi_keywords": ["Wehrpflicht", "Bundeswehr", "Wehrdienst", "mandatory military"]
    },
    "retirement_age": {
        "label": "Retirement at 70",
        "emoji": "👴",
        "newsapi_keywords": ["Rente mit 70", "Renteneintrittsalter", "Rentenreform", "Rente", "Rentenalter"]
    },
    "speed_limit": {
        "label": "Autobahn Speed Limit",
        "emoji": "🚗",
        "newsapi_keywords": ["Tempolimit", "Autobahn", "Geschwindigkeitsbegrenzung", "130 km/h"]
    },
    "euthanasia": {
        "label": "Assisted Dying",
        "emoji": "💉",
        "newsapi_keywords": ["Sterbehilfe", "Euthanasie", "assistierter Suizid", "Sterbebegleitung"]
    },
    "wealth_tax": {
        "label": "Wealth Tax",
        "emoji": "💸",
        "newsapi_keywords": ["Vermögenssteuer", "Reichensteuer", "wealth tax", "Vermögensabgabe"]
    },
    "ai_jobs": {
        "label": "AI Replacing Jobs",
        "emoji": "🤖",
        "newsapi_keywords": ["KI Arbeitsplätze", "Automatisierung", "AI jobs", "KI ersetzt", "Jobverlust KI"]
    },
    "ai_regulation": {
        "label": "AI Regulation & Ethics",
        "emoji": "🧠",
        "newsapi_keywords": ["KI Regulierung", "AI regulation", "EU AI Act", "KI Ethik", "Künstliche Intelligenz Gesetz"]
    },
}