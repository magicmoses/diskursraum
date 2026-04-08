"""
topics.py — Core discussion topics for ConsensusAgent

These topics represent polarizing societal debates in Germany
where bridging statements across ideological groups are most valuable.
"""

TOPICS = {
    "migration": {
        "label": "Migration & Asylpolitik",
        "description": "Einwanderung, Asylrecht und Integration — eines der polarisierendsten Themen Deutschlands",
        "emoji": "🌍",
    },
    "energy_transition": {
        "label": "Energiewende",
        "description": "Atomkraft, erneuerbare Energien und Klimapolitik — zwischen Versorgungssicherheit und Klimaschutz",
        "emoji": "⚡",
    },
    "retirement": {
        "label": "Rente & Altersvorsorge",
        "description": "Rentenpolitik, Rentenalter und Generationengerechtigkeit als gesellschaftliche Dauerdebatte",
        "emoji": "👴",
    },
    "wealth_tax": {
        "label": "Vermögenssteuer & Umverteilung",
        "description": "Besteuerung großer Vermögen, Erbschaftssteuer und soziale Gerechtigkeit",
        "emoji": "💸",
    },
    "digitalization": {
        "label": "Digitale Transformation & KI",
        "description": "Digitalisierung, Künstliche Intelligenz und gesellschaftlicher Wandel durch Technologie",
        "emoji": "🤖",
    },
}

FUTURE_TOPICS = {
    "basic_income":   "Grundeinkommen & Bürgergeld",
    "military_service": "Wehrpflicht",
    "speed_limit":    "Tempolimit Autobahn",
    "euthanasia":     "Sterbehilfe",
    "ai_regulation":  "KI Regulierung (EU AI Act)",
    "ai_jobs":        "KI & Arbeitsmarkt",
}