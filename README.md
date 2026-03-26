# ConsensusAgent 🦞

> A multi-agent AI system that inverts the engagement algorithm — surfacing statements
> that bridge opinion groups rather than divide them.

Inspired by Taiwan's [vTaiwan](https://info.vtaiwan.tw/) civic deliberation platform
and the [Pol.is](https://pol.is) bridging algorithm.

## What it does

ConsensusAgent analyzes public discourse on controversial topics and identifies
**bridging statements** — content that finds approval across ideologically distinct
user clusters, not just within echo chambers.

This is the opposite of how social media algorithms typically work.

## Topics analyzed

| Topic | Data Source | Notes |
|-------|-------------|-------|
| 🇩🇪 Migration & Asylum Policy | Reddit (r/de, r/germany, r/europe) | |
| 💰 Unconditional Basic Income | Reddit (r/de, r/BasicIncome, r/germany) | |
| ⚛️ Nuclear Energy | Reddit + Pol.is Taiwan | Cross-cultural comparison 🔥 |
| 🪖 Mandatory Military Service | Reddit (r/de, r/germany) | High recency, active debate |
| 👴 Retirement at 70 | Reddit (r/de, r/finanzen) | Generational cluster split |
| 🚗 Autobahn Speed Limit | Reddit (r/de, r/germany) | German identity debate |
| 💉 Assisted Dying / Euthanasia | Reddit (r/de, r/ethik) | Ethics polarization |
| 💸 Wealth Tax | Reddit (r/de, r/wirtschaft) | Class-based clusters |
| 🤖 AI Replacing Jobs | Reddit (r/Futurology, r/de, r/artificial) | Generational + industry clusters |
| 🧠 AI Regulation & Ethics | Pol.is Taiwan (vTaiwan 2023) | IT context, Taiwanese dataset |

## Architecture
```
OpenClaw (trigger + data collection)
    └── CrewAI Pipeline (4 agents)
            ├── Collector Agent    — fetches Reddit / Pol.is data
            ├── Clusterer Agent    — groups opinions via embeddings
            ├── Bridging Analyst   — scores cross-cluster approval
            └── Reporter Agent     — structured JSON output
                    └── Ollama (local LLM — no cloud dependency)

React Frontend — topic selector + cluster visualization
FastAPI         — bridge between frontend and crew pipeline
```

## Tech Stack

- **[OpenClaw](https://openclaw.ai)** — agentic trigger layer & skill system
- **[CrewAI](https://crewai.com)** — multi-agent orchestration
- **[Ollama](https://ollama.ai)** — local LLM inference (Llama 3.1)
- **[PRAW](https://praw.readthedocs.io)** — Reddit data collection
- **[Pol.is Open Data](https://github.com/compdemocracy/openData)** — vTaiwan datasets
- **React + D3.js** — cluster visualization frontend
- **FastAPI** — REST bridge between frontend and agent pipeline

## How the bridging score works

Traditional social media rewards content that maximizes engagement within a group.
ConsensusAgent rewards content that finds approval *across* groups.
```
1. Raw comments are embedded into vector space
2. K-Means clustering groups users by opinion similarity
3. Each statement is scored: how many distinct clusters approve?
4. High bridging score = consensus potential, not virality
```

This logic is directly inspired by the Pol.is algorithm used in Taiwan's
vTaiwan platform, where it helped resolve deadlocked policy debates on
Uber regulation, FinTech legislation, and AI governance.

## Setup
```bash
# 1. Clone & install
git clone https://github.com/AyzennaMosesArndt/consensus-agent.git
cd consensus-agent
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# → fill in your Reddit API credentials (see Reddit App setup below)

# 3. Start Ollama (separate terminal)
ollama pull llama3.1
ollama serve

# 4. Run analysis
python api/run_crew.py --topic "nuclear_energy" --source reddit

# 5. Start frontend
cd frontend
npm install
npm run dev
```

## Reddit API Setup

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click **Create App** → select **script**
3. Copy `client_id` and `client_secret` into your `.env`

## Data Sources

**Reddit (PRAW)** — live data fetched per analysis run, cached locally in `data/reddit/`

**Pol.is / vTaiwan Open Data** — static CSVs from the
[Computational Democracy Project](https://github.com/compdemocracy/openData),
stored in `data/polis/`. Covers real citizen deliberations on Uber regulation,
FinTech, and AI governance in Taiwan.

## Background

This project is inspired by the work of Audrey Tang and the g0v civic tech community
in Taiwan, who demonstrated that algorithmic design choices in social platforms are
not neutral — and that inverting them toward consensus rather than engagement
produces meaningfully different (and healthier) public discourse.

The concept is explored in depth in the book
[Plurality](https://www.plurality.net/) by Audrey Tang and E. Glen Weyl.

## Status

🚧 Active development — March 2026