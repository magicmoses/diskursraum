# Diskursraum 🎙️

> Mapping Public Discourse in Germany — inspired by Taiwan's vTaiwan and the Pol.is bridging algorithm.

**[Live Demo](https://deine-vercel-url.vercel.app)** · [GitHub](https://github.com/AyzennaMosesArndt/diskursraum)

---

## What is Diskursraum?

Diskursraum makes German public discourse visible across two dimensions:

**Dimension I — Medienspiegel:** How do 15 German news outlets cover polarizing societal topics? Where is there consensus — and where does discourse begin?

**Dimension II — Parteienspiegel:** How have party positions evolved across six federal elections from 2005 to 2025? Who converges, who diverges — and what do election results say about it?

Inspired by [Plurality](https://www.plurality.net/) (Audrey Tang & E. Glen Weyl) and the [Pol.is](https://pol.is) bridging algorithm from Taiwan's vTaiwan platform — applied to the German media and political landscape.

---

## Dimension I — Medienspiegel

For each of five topics, the app shows:
- **Political Spectrum** — which bias groups cover the topic and how extensively
- **Shared Perspectives** — what all outlets agree on despite different political leanings
- **Controversial Points** — where coverage diverges most strongly
- **Emotional Tone** — which emotions dominate the reporting of each outlet

| Topic | Description |
|-------|-------------|
| Migration & Asylum Policy | Immigration, asylum law, integration |
| Energy Transition | Nuclear power, renewables, climate policy |
| Pension & Retirement | Pension reform, retirement age, generational justice |
| Wealth Tax | Redistribution, inheritance tax, fiscal justice |
| Digital Transformation | AI, digitalization, societal change |

---

## Dimension II — Parteienspiegel

Semantic analysis of all Bundestagswahlprogramme from 2005 to 2025:

- **Bridging Score** — semantic centrality per party per topic: who bridges across ideological lines?
- **Force-Directed Graph** — party similarity network per year and topic
- **Pairwise Heatmap** — 6×6 similarity matrix, switchable by topic
- **PCA Trajectories** — party movement in shared 2D semantic space across elections
- **Historical Timeline** — annotated with key events: "Finanzkrise", "Flüchtlingskrise", "Corona", "AfD-Bundestagseinzug", "Ampel-Bruch"
- **Election Results** — correlation analysis with bridging & party movement analysis
- **ManifestoBERTa Classification** — 56 policy categories per party per year

| Metric | Coverage |
|--------|----------|
| Parties | CDU/CSU, SPD, Grüne, FDP, AfD, Die Linke |
| Elections | 2005, 2009, 2013, 2017, 2021, 2025 |
| Embedding Model | intfloat/multilingual-e5-base |
| Classification | manifesto-project/manifestoberta-xlm-roberta-56policy-topics-context-2024-1-1 |

---

## Architecture

```
Dimension I — Medienspiegel
  RSS Crawler (4× daily, GitHub Actions)
    └── 19 German news sources → SQLite DB

  ML Pipeline (every 3 days, GitHub Actions, 04:00 UTC)
    ├── Sentence Embeddings    (intfloat/multilingual-e5-base)
    ├── Sentiment Analysis     (oliverguhr/german-sentiment-bert)
    ├── Emotion Detection      (AnasAlokla/multilingual_go_emotions_V1.2)
    ├── Medienspiegel Analysis
    │   ├── Broad Retrieval    (keyword matching)
    │   ├── LLM Relevance Filter (Groq llama-3.3-70b)
    │   ├── Per-Outlet Aggregation
    │   └── LLM Synthesis      (shared perspectives + controversial points)
    └── JSON Export → committed to repo

Dimension II — Parteienspiegel
  Manifesto Pipeline (local, run per election year)
    ├── PDF Processing         (LangChain SemanticChunker)
    ├── ChromaDB Storage       (intfloat/multilingual-e5-base embeddings)
    ├── RAG per Topic          (Query Expansion + Contextual Compression via Groq)
    ├── Bridging Scores        (Cosine Similarity + NetworkX graph)
    ├── LLM Analysis           (party summaries + cross-party synthesis)
    ├── ManifestoBERTa         (56 policy category classification)
    └── Historical Analysis    (PCA, bridging timeseries, election result correlation)

Backend (FastAPI / Railway)
  └── Serves pre-computed JSON — stateless, no DB in production

Frontend (React + Vite / Vercel)
  ├── Landing         — Project overview
  ├── Medienspiegel   — Topic analysis + media statistics
  ├── Parteienspiegel — Party position analysis (4 tabs)
  └── Project         — Crawl stats + technical metrics
```

Diskursraum follows a static-first architecture: all analysis results are pre-computed offline, committed as JSON to the repository, and served directly by the API — eliminating runtime database load for the core application.
---

<img width="3537" height="1766" alt="Diskursraum - Overview" src="https://github.com/user-attachments/assets/d07511e1-074d-46c5-b3e3-5cfc561f4fa3" />

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Vite, D3.js, Recharts |
| Backend | FastAPI, Python 3.11 |
| ML/NLP | sentence-transformers, germansentiment, transformers |
| LLM | Groq (llama-3.3-70b-versatile), Anthropic Claude Haiku (fallback) |
| Vector DB | ChromaDB |
| Graph Analysis | NetworkX |
| Classification | ManifestoBERTa (Manifesto Project) |
| Database | SQLite |
| Pipeline | GitHub Actions |
| Deployment | Vercel (Frontend) + Railway (Backend) |

---

## Data Sources

### News (Dimension I)
Arcticles crawled from RSS-Feeds of 19 German news outlets over _____ & annoteted with bias labels:

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
Bundestagswahlprogramme 2005–2025, locally stored as PDF.
Election results: Bundestag (bundestag.de), Bundeswahlleiterin, wahlrecht.de

---

  ---
  Populism Score

  Diskursraum measures populist rhetoric in party manifestos using a
  sentence-level classifier, benchmarked against the
  https://komm.uni-hohenheim.de/wahlprogramm-analyse — the University of
  Hohenheim's long-running analysis of German election programs for
  linguistic quality and rhetorical strategies.

  Method

  Every sentence across all manifesto chunks (2005–2025) is classified by
  https://huggingface.co/przvl/PopEuroBERT-binary-610m, a fine-tuned
  EuroBERT-610M model trained on the PopBERT dataset of sentence-level
  annotated German Bundestag speeches (Erhard et al., 2025).

  ▎ Populism score = share of sentences with a populist probability > 0.43

  Why threshold 0.43? The decision boundary was calibrated on the PopBERT
  test set for balanced performance: precision 76.6%, recall 85.8%, F1
  80.9%. A threshold below 0.5 is appropriate because underdetecting
  populist language in dense political texts carries a higher cost than
  occasional false positives.

  References

  - Erhard, L., Hanke, S., Remer, U., Falenska, A., & Heiberger, R. H.
  (2025). PopBERT. Detecting Populism and Its Host Ideologies in the German
  Bundestag. Political Analysis, 33(1), 1–17.
  https://doi.org/10.1017/pan.2024.12
  - Boizard, N. et al. (2025). EuroBERT: Scaling Multilingual Encoders for
  European Languages. arXiv:2503.05500. https://arxiv.org/abs/2503.05500
  - przvl (2025). PopEuroBERT-binary-610m. Hugging Face.
  https://huggingface.co/przvl/PopEuroBERT-binary-610m
  - Brettschneider, F. et al. (2025). Hohenheimer Analyse der Wahlprogramme
  zur Bundestagswahl 2025. Universität Hohenheim.
  https://komm.uni-hohenheim.de/wahlprogramm-analyse

---

## Local Development

```bash
# Clone repository
git clone https://github.com/AyzennaMosesArndt/diskursraum.git
cd diskursraum

# Python environment
conda create -n diskursraum python=3.11
conda activate diskursraum
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Set GROQ_API_KEY, ANTHROPIC_API_KEY, LLM_PROVIDER

# Start backend
cd api && uvicorn main:app --reload --port 8001

# Start frontend
cd frontend && npm install && npm run dev
```

## Deployment

Diskursraum runs fully stateless in production:
- **Railway** hosts the FastAPI backend
- **Vercel** hosts the React frontend
- All analysis results are pre-computed, committed as JSON, and served directly — no database connection required in production

---

## Status

🚧 Active development — spring 2026

---

## Author

**Ayzenna Moses Arndt** — M.Sc. Business Informatics, HKA Karlsruhe  
[GitHub](https://github.com/AyzennaMosesArndt) · [LinkedIn](https://linkedin.com/in/dein-profil)

---

## Methodology

> *"In Mandarin, 數位 means both 'digital' and 'plural.' To be plural is to be digital. To be digital is to be plural."*  
> — Audrey Tang & E. Glen Weyl, Plurality

Diskursraum makes this principle visible — not for social media posts as in Pol.is, but for professional media discourse in Germany. Many voices, one discourse.
