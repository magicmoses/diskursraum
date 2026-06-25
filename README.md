# Diskursraum 🎙️

> Mapping Public Discourse in Germany — inspired by [Plurality](https://www.plurality.net/) (Audrey Tang & E. Glen Weyl) and the [Pol.is](https://pol.is) bridging algorithm from Taiwan's vTaiwan platform

> *"In Mandarin, 數位 means both 'digital' and 'plural.' To be plural is to be digital. To be digital is to be plural."*
> — Audrey Tang & E. Glen Weyl, Plurality

Diskursraum makes this principle visible. Not for social media posts as in Pol.is, but for professional media discourse in Germany. Many voices, one discourse.

![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-9135FF?style=for-the-badge&logo=vite&logoColor=white)
![D3.js](https://img.shields.io/badge/D3.js-F9A03C?style=for-the-badge&logo=d3&logoColor=white)
![Recharts](https://img.shields.io/badge/Recharts-8884d8?style=for-the-badge)
![react-i18next](https://img.shields.io/badge/react--i18next-26A69A?style=for-the-badge)

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-9B59B6?style=for-the-badge)

![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Groq](https://img.shields.io/badge/Groq-3B3B3B?style=for-the-badge)
![Anthropic](https://img.shields.io/badge/Anthropic_Claude-191919?style=for-the-badge&logo=anthropic&logoColor=white)

![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)


**[Live Demo](https://diskursraum.vercel.app)** · [GitHub](https://github.com/magic-moses/diskursraum)

---

## What is Diskursraum?

Diskursraum makes German public discourse visible across three dimensions:

**Dimension I — Medienspiegel:** How do 19 German news outlets cover polarizing societal topics (tracked since March 2026)? Where is there consensus & where does discourse begin? 

**Dimension II — Parteienspiegel:** How have party positions evolved across six federal elections from 2005 to 2025? Who converges, who diverges & what do the election results say about it?

**Dimension III — Frag nach.:** Ask the party manifestos directly. Semantic search across all Bundestagswahlprogramme 2005–2025 with LLM-generated answers.

Inspired by [Plurality](https://www.plurality.net/) (Audrey Tang & E. Glen Weyl) and the [Pol.is](https://pol.is) bridging algorithm from Taiwan's vTaiwan platform — applied to the German media and political landscape.

---

## Architecture

<img width="3562" height="1754" alt="01_overview" src="https://github.com/user-attachments/assets/e90af083-aa3a-4c2b-82dc-0b8046e95276" />

Diskursraum follows a **static-first architecture**: all analysis results are pre-computed offline, committed as JSON to the repository, and served directly by the API, eliminating runtime database load for the core application. The only live path is Dimension III (Frag nach./(engl.: Ask.), which queries pgvector in real time via RAG.

### Storage

Diskursraum uses three distinct storage layers:

<img width="3654" height="1710" alt="03_storage_view" src="https://github.com/user-attachments/assets/fa84563c-dcfa-4144-9c5f-40bb5b8705ee" />

**PostgreSQL on Railway (pgvector)** is the live single source of truth. It stores all crawled articles with embeddings, sentiment and emotion scores, plus the `manifesto_chunks` table used for semantic search in Dimension III. Party manifesto chunks were initially stored in ChromaDB (local) and later migrated to pgvector for production search.

**ChromaDB (local, gitignored)** is used during the manifesto analysis pipeline (BridgingScore, ManifestoBERTa, PopEuroBERT). It runs once per election cycle (~every 4 years) and is not present in production.

**Pre-computed JSON (GitHub repo, `data/results/`)** contains all analysis results committed as static files and served directly by the API.

---
## Dimensional view

<img width="4045" height="1544" alt="02_dimensional_view" src="https://github.com/user-attachments/assets/d8f4a077-a9f2-487a-b3dd-5cbcb226f5da" />


## Dimension I — Medienspiegel

> Coverage data spans from March 2026 to present, crawled 4× daily from RSS feeds.

For each of eight topics, the app shows:

- **Political Spectrum** — which bias groups cover the topic and how extensively
- **Shared Perspectives** — what all outlets agree on despite different political leanings
- **Controversial Points** — where coverage diverges most strongly, contextualized against shared perspectives
- **Emotional Tone** — which emotions dominate the reporting of each outlet

| Topic | Description |
|-------|-------------|
| Migration & Asylum Policy | Immigration, asylum law, integration |
| Energy Transition | Nuclear power, renewables, climate policy |
| Pension & Retirement | Pension reform, retirement age, generational justice |
| Digital Transformation | AI, digitalization, societal change |
| Work in Transition | Labour market, remote work, automation |
| Defense & Military | Rearmament, NATO, Zeitenwende |
| Family & Children | Family policy, childcare, parental leave |
| Education | Schools, universities, lifelong learning |

---

## Dimension II — Parteienspiegel

Semantic analysis of all Bundestagswahlprogramme from 2005 to 2025:

- **Ideological Matrix** — party positions on two axes: economy (left/right) and society (conservative/progressive), derived from ManifestoBERTa category weights
- **Proximity & Distance** — pairwise programmatic similarity, 6x6 heatmap, switchable by year
- **Bridge Builder Score** — semantic centrality per party: who bridges across ideological lines? Combines PCA on multilingual-e5-base embeddings (40%) and Weighted Jaccard similarity on ManifestoBERTa category distributions (60%), aggregated as betweenness centrality via NetworkX. A high score indicates a party whose manifesto content sits close to multiple ideologically distinct parties simultaneously — bridging rather than polarising.
- **Similarity Network** — force-directed graph of party similarity per election year
- **Historical Timeline** — annotated with key events: Finanzkrise, Flüchtlingskrise, Corona, AfD-Bundestagseinzug, Ampel-Bruch
- **Election Results** — Bundestagswahl Zweitstimmen 2005–2025
- **ManifestoBERTa Classification** — 56 policy categories per party per year
- **HIX Readability Score** — Hohenheim Readability Index per party per year
- **Populism Score** — sentence-level populist rhetoric detection via PopEuroBERT
- **Program Length** — word count per party per election year

Beyond classification and scoring, the manifesto pipeline derives an ideological position for each party per election year mapping programmatic emphasis onto a two-dimensional space (economy and society) directly from ManifestoBERTa category weights. Party trajectories, pairwise similarity heatmaps, and a force-directed similarity network visualise how the six parties have moved toward or away from each other across twenty years of German federal elections.

| Metric | Coverage |
|--------|----------|
| Parties | CDU/CSU, SPD, Grüne, FDP, AfD, Die Linke |
| Elections | 2005, 2009, 2013, 2017, 2021, 2025 |
| Embedding model | intfloat/multilingual-e5-base |
| Classification | manifesto-project/manifestoberta-xlm-roberta-56policy-topics-context-2024-1-1 |
| Populism model | przvl/PopEuroBERT-binary-610m |
| Readability | Hohenheim Readability Index (HIX), Brettschneider/Thoms |

---

## Dimension III — Frag nach.

Ask the party manifestos directly. Enter a free-text question — Diskursraum detects party and year from your query, searches the manifesto chunks via pgvector cosine similarity, and generates a streamed LLM answer with source citations.

- Semantic search across all Bundestagswahlprogramme 2005–2025
- Automatic party and year detection from free-text input
- Streamed answers via Groq llama-3.3-70b with Claude Haiku-4.5 fallback
- Rate limiting: 10 deep-dives per session, 50 per IP per day

---

## Populism Score

Diskursraum measures populist rhetoric in party manifestos using a sentence-level classifier, benchmarked against the [Hohenheimer Wahlprogramm-Analyse](https://komm.uni-hohenheim.de/wahlprogramm-analyse) — the University of Hohenheim's long-running analysis of German election programs for linguistic quality and rhetorical strategies.

**Method:** Every sentence across all manifesto chunks (2005–2025) is classified by [przvl/PopEuroBERT-binary-610m](https://huggingface.co/przvl/PopEuroBERT-binary-610m), a fine-tuned EuroBERT-610M model trained on the PopBERT dataset of sentence-level annotated German Bundestag speeches (Erhard et al., 2025). As the exact Hohenheim model is not publicly available, PopEuroBERT was selected as the methodologically closest available model, enabling consistent scores across all election years 2005–2025.

> Populism score = share of sentences with a populist probability > 0.43

**Why threshold 0.43?** The decision boundary was calibrated on the PopBERT test set for balanced performance: precision 76.6%, recall 85.8%, F1 80.9%. A threshold below 0.5 is appropriate because underdetecting populist language in dense political texts carries a higher cost than occasional false positives.

**References:**
- Erhard, L., Hanke, S., Remer, U., Falenska, A., & Heiberger, R. H. (2025). PopBERT. Detecting Populism and Its Host Ideologies in the German Bundestag. *Political Analysis*, 33(1), 1–17. https://doi.org/10.1017/pan.2024.12
- Boizard, N. et al. (2025). EuroBERT: Scaling Multilingual Encoders for European Languages. arXiv:2503.05500. https://arxiv.org/abs/2503.05500
- przvl (2025). PopEuroBERT-binary-610m. Hugging Face. https://huggingface.co/przvl/PopEuroBERT-binary-610m
- Brettschneider, F. et al. (2025). Hohenheimer Analyse der Wahlprogramme zur Bundestagswahl 2025. Universität Hohenheim. https://komm.uni-hohenheim.de/wahlprogramm-analyse

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Vite, D3.js, Recharts, react-i18next |
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL + pgvector (Railway) |
| ML/NLP | sentence-transformers, german-sentiment-bert, go_emotions_V1.2 |
| LLM | Groq llama-3.3-70b-versatile, Anthropic Claude Haiku-4.5 (fallback) |
| Vector search | pgvector (production), ChromaDB (local pipeline) |
| Graph analysis | NetworkX |
| Classification | ManifestoBERTa (Manifesto Project) |
| Populism scoring | PopEuroBERT-binary-610m |
| Pipeline | GitHub Actions |
| Deployment | Vercel (frontend), Railway (backend + PostgreSQL) |

---

## Data Sources

### News (Dimension I)

Articles crawled from RSS feeds of 19 German news outlets since March 2026, annotated with bias labels:

| Bias | Outlets |
|------|---------|
| Left | taz |
| Left-Liberal | Spiegel, Zeit, SZ, Stern |
| Neutral | Tagesschau, ZDF, DW |
| Conservative-Liberal | FAZ, Cicero, NZZ-Deutschland |
| Right-Conservative | WELT, Focus, n-tv |
| Far-Right | Junge Freiheit, Tichys Einblick, Achse des Guten |
| Economic-Liberal | Handelsblatt |
| Populist-Mixed | BILD |

### Party Manifestos (Dimension II)

Bundestagswahlprogramme 2005–2025, sourced as PDF from official party websites. Election results from Bundeswahlleiterin and wahlrecht.de. HIX readability scores from Universität Hohenheim, Wahlprogramm-Check (Brettschneider/Thoms).

---

## Local Development

```bash
git clone https://github.com/magic-moses/diskursraum.git
cd diskursraum

conda create -n diskursraum python=3.11
conda activate diskursraum
pip install -r requirements.txt

cp .env.example .env
# Set GROQ_API_KEY, ANTHROPIC_API_KEY, RAILWAY_DATABASE_URL

cd api && uvicorn main:app --reload --port 8001
cd frontend && npm install && npm run dev
```

---

## Deployment

- **Railway** — FastAPI backend + PostgreSQL with pgvector
- **Vercel** — React frontend
- **GitHub Actions** — `daily_crawl.yml` (4x daily) + `daily_ml.yml` (every 3 days)

---

## Author

[GitHub](https://github.com/magic-moses)
---
