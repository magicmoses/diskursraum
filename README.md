# Diskursraum 🎙️

> Mapping Public Discourse in Germany — inspired by Taiwan's vTaiwan and the Pol.is bridging algorithm.

**[Live Demo](https://deine-vercel-url.vercel.app)** · [GitHub](https://github.com/AyzennaMosesArndt/consensus-agent)

---

## What is Diskursraum?

Diskursraum analyzes how 15 German news outlets cover polarizing societal topics. The goal is transparency about media diversity in an increasingly polarized public discourse.

For each topic, the app shows:
- **Political Spectrum** — which bias groups cover the topic and how extensively
- **Shared Perspectives** — what all outlets agree on despite different political leanings
- **Controversial Points** — where coverage diverges most strongly
- **Emotional Tone** — which emotions dominate the reporting of each outlet

Inspired by [Plurality](https://www.plurality.net/) (Audrey Tang & E. Glen Weyl) and the [Pol.is](https://pol.is) bridging algorithm from Taiwan's vTaiwan platform — applied to the German media landscape.

---

## Topics

| Topic | Description |
|-------|-------------|
| 🌍 Migration & Asylum Policy | Immigration, asylum law, integration |
| ⚡ Energy Transition | Nuclear power, renewables, climate policy |
| 👴 Pension & Retirement | Pension reform, retirement age, generational justice |
| 💸 Wealth Tax | Redistribution, inheritance tax, fiscal justice |
| 🤖 Digital Transformation | AI, digitalization, societal change |

---

## Architecture
```
RSS Crawler (8x daily, GitHub Actions)
  └── 15 German news sources → SQLite DB

Daily ML Pipeline (GitHub Actions, 04:00 UTC)
  ├── Sentence Embeddings    (jinaai/jina-embeddings-v2-base-de)
  ├── Sentiment Analysis     (oliverguhr/german-sentiment-bert)
  ├── Emotion Detection      (AnasAlokla/multilingual_go_emotions_V1.2)
  ├── Medienspiegel Analysis
  │   ├── Broad Retrieval    (keyword matching, title + text)
  │   ├── LLM Relevance Filter (Groq llama-3.3-70b)
  │   ├── Per-Outlet Aggregation
  │   └── LLM Synthesis      (shared perspectives + controversial points)
  └── JSON Export → committed to repo → triggers Vercel redeploy

Backend (FastAPI / Railway)
  └── Serves pre-computed JSON — stateless, no DB in production

Frontend (React + Vite / Vercel)
  ├── Home        — Topic Overview
  ├── Analytics   — Media Statistics & Emotion Analysis
  └── TopicView   — Medienspiegel per Topic
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Vite, Tailwind CSS, Recharts |
| Backend | FastAPI, Python 3.11 |
| ML/NLP | sentence-transformers, germansentiment, transformers |
| LLM | Groq (llama-3.3-70b-versatile) / Ollama (local) |
| Database | SQLite |
| Pipeline | GitHub Actions |
| Deployment | Vercel (Frontend) + Railway (Backend) |

---

## Data Sources

15 German news outlets with bias labels:

| Bias | Outlets |
|------|---------|
| Left | taz |
| Left-Liberal | Spiegel, Zeit, SZ, Stern |
| Neutral | Tagesschau, ZDF, DW |
| Conservative-Liberal | FAZ, Cicero |
| Right-Conservative | WELT, Focus |
| Far-Right | Junge Freiheit |
| Economic-Liberal | Handelsblatt |
| Populist-Mixed | BILD |

---

## Local Development
```bash
# Clone repository
git clone https://github.com/AyzennaMosesArndt/consensus-agent.git
cd consensus-agent

# Python environment
conda create -n consensus-agent python=3.11
conda activate consensus-agent
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Set GROQ_API_KEY and LLM_PROVIDER

# Optional: Ollama for local LLM inference
ollama pull llama3.1
ollama serve

# Start backend
cd api && uvicorn main:app --reload --port 8001

# Start frontend
cd frontend && npm install && npm run dev
```

---

## Deployment

Diskursraum runs fully stateless in production:
- **Railway** hosts the FastAPI backend
- **Vercel** hosts the React frontend
- All analysis results are pre-computed daily, committed as JSON, and served directly by the backend — no database connection required in production

---

## Roadmap

- [ ] **Party Manifesto Integration** — German party programs as a second data source; compare media coverage vs. party positions (Vector DB, PDF parsing)
- [ ] **Bridging Statements** — LLM-based extraction of specific statements that find approval across ideological groups
- [ ] **Time Series** — How does coverage of a topic evolve over time?
- [ ] **More Topics** — Military service, speed limit, assisted dying, AI regulation, basic income

---

## Methodology

> *"In Mandarin, 數位 means both 'digital' and 'plural.' To be plural is to be digital. To be digital is to be plural. Plurality captures the symbiotic relationship between democracy and collaborative technology. Together, democracy and collaborative technology can power infinite diversity in infinite combinations. Let's free the future — together."*  
> — Audrey Tang & E. Glen Weyl, Plurality

Diskursraum makes this principle visible — not for social media posts as in Pol.is, but for professional media discourse in Germany. Many voices, one discourse.

---

## Status

🚧 Active development — April 2026

---

## Author

**Ayzenna Moses Arndt** — M.Sc. Business Informatics, HKA Karlsruhe  
[GitHub](https://github.com/AyzennaMosesArndt) · [LinkedIn](https://linkedin.com/in/dein-profil)