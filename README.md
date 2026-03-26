# ConsensusAgent 🦞

> A multi-agent AI system that inverts the engagement algorithm — surfacing statements
> that bridge opinion groups rather than divide them.

Inspired by Taiwan's [vTaiwan](https://info.vtaiwan.tw/) civic deliberation platform
and the [Pol.is](https://pol.is) bridging algorithm — but applied to real-time public
discourse across news, social media, and video comments.

## What it does

ConsensusAgent analyzes public discourse on controversial topics and identifies
**bridging statements** — content that finds approval across ideologically distinct
user clusters, not just within echo chambers.

This is the opposite of how social media algorithms typically work.

## Topics analyzed

| Topic | Notes |
|-------|-------|
| 🇩🇪 Migration & Asylum Policy | |
| 💰 Unconditional Basic Income | |
| ⚛️ Nuclear Energy | International sources included |
| 🪖 Mandatory Military Service | |
| 👴 Retirement at 70 | Generational cluster split |
| 🚗 Autobahn Speed Limit | German identity debate |
| 💉 Assisted Dying / Euthanasia | |
| 💸 Wealth Tax | |
| 🤖 AI Replacing Jobs | |
| 🧠 AI Regulation & Ethics | Tech-focused sources |

## Data Sources

ConsensusAgent pulls from three complementary layers of public discourse:

| Source | Type | Coverage |
|--------|------|----------|
| [NewsAPI](https://newsapi.org) | News articles | Spiegel, Zeit, FAZ, Tagesschau, BBC, Reuters |
| [Bluesky AT Protocol](https://atproto.com) | Social media posts | Open API, no scraping |
| [YouTube Data API v3](https://developers.google.com/youtube) | Video comments | ARD, ZDF, MrWissen2go, DW |

> **Demo mode**: Pre-cached datasets ship with the repo — no API keys needed
> to explore the interface and results.

## Architecture
```
OpenClaw (trigger + data collection skills)
    └── CrewAI Pipeline (4 agents)
            ├── Collector Agent    — fetches from NewsAPI / Bluesky / YouTube
            ├── Clusterer Agent    — groups opinions via sentence embeddings
            ├── Bridging Analyst   — scores cross-cluster approval
            └── Reporter Agent     — structured JSON output
                    └── Ollama (local) or Groq (cloud/demo)

React Frontend — topic selector + cluster visualization
FastAPI         — REST bridge between frontend and agent pipeline
```

## Tech Stack

- **[OpenClaw](https://openclaw.ai)** — agentic trigger layer & skill system
- **[CrewAI](https://crewai.com)** — multi-agent orchestration
- **[Ollama](https://ollama.ai)** — local LLM inference (Llama 3.1)
- **[Groq](https://groq.com)** — cloud LLM inference (demo mode)
- **[NewsAPI](https://newsapi.org)** — news article data
- **[Bluesky AT Protocol](https://atproto.com)** — social media data
- **[YouTube Data API v3](https://developers.google.com/youtube)** — video comment data
- **React + D3.js** — cluster visualization frontend
- **FastAPI** — REST bridge between frontend and agent pipeline

## How the bridging score works

Traditional social media rewards content that maximizes engagement within a group.
ConsensusAgent rewards content that finds approval *across* groups.
```
1. Raw text (articles, posts, comments) embedded into vector space
2. K-Means clustering groups content by opinion similarity  
3. Each statement scored: how many distinct clusters approve?
4. High bridging score = consensus potential, not virality
```

Conceptually inspired by the [Pol.is](https://pol.is) algorithm used in Taiwan's
vTaiwan platform — adapted here for multi-source, real-time discourse analysis.

## Setup
```bash
# 1. Clone & install
git clone https://github.com/AyzennaMosesArndt/consensus-agent.git
cd consensus-agent
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# → fill in API keys (or leave as-is for demo mode)

# 3. Start Ollama (optional — only needed for local LLM mode)
ollama pull llama3.1
ollama serve

# 4. Run analysis
python api/run_crew.py --topic "nuclear_energy"

# 5. Start frontend
cd frontend
npm install
npm run dev
```

## Modes

| Mode | LLM | Data | Use case |
|------|-----|------|----------|
| Demo | Groq (cloud) | Pre-cached JSON | Recruiters, quick explore |
| Live | Ollama (local) | Live API calls | Full local run |

## Background

This project is inspired by the work of Audrey Tang and the g0v civic tech community
in Taiwan, who demonstrated that algorithmic design choices in social platforms are
not neutral — and that inverting them toward consensus rather than engagement
produces meaningfully different (and healthier) public discourse.

The concept is explored in depth in the book
[Plurality](https://www.plurality.net/) by Audrey Tang and E. Glen Weyl.

## Status

🚧 Active development — March 2026