# Reuse Decisions & Functional Capability Comparison

## 1. Executive Summary of Reuse Decisions

Following a systematic 5-pillar audit across licensing, security, modularity, code quality, and maintainability, the nine candidate repositories are classified as follows:

- **REUSE (1)**: `Anurag9557/cricket-iq` (Exemplary Polars chase state builder, verification gate, LightGBM win probability, MIT license).
- **ADAPT (2)**: 
  - `HalcyonVector/Cricket-Intelligence-Lab` (Next.js streaming JSON extraction heuristic for Cricbuzz; Cricsheet `orjson` parser).
  - `ZainZoy/NLP-project` (Deterministic commentary grammar, accuracy-first scoring conventions, score validation gate).
- **REFERENCE ONLY (3)**:
  - `SRIHARI18V/CRICKET-RAG-CHATBOT` (Hybrid query router separating structured stats path from narrative path).
  - `vinaybale-collab/cricket-analytics-web` (DuckDB analytical SQL patterns, Next.js UI component design).
  - `princyhareshbhai1530/T20-Commentary-Analysis` (Domain excitement keyword lists).
- **REJECT (3)**:
  - `sst-cloud-solutions/h25-sports` (**Hard License Blocker**: explicitly declared `UNLICENSED - Private project`; copyright prohibition on code reuse).
  - `Paul-ans-typ/Analysis-of-Cricket-Commentary` (Anti-pattern: predicting scores from commentary via unverified pickled RNN models).
  - `ShrinathSontakke/Cricket-Data-Analytics` (Proprietary binary PowerBI `.pbix` formats, external paid proxy scrapers).

---

## 2. Feature-by-Feature Capability Comparison

| Platform Capability | Candidate Implementations Evaluated | Strongest Implementation | Decision & Technical Justification |
| :--- | :--- | :--- | :--- |
| **01. News & Journalism Ingestion** | **None** of the 9 repositories ingest editorial news articles, previews, or reviews. | **NONE (Must build from scratch)** | Build native polite crawler using `trafilatura` + `BeautifulSoup4` with `robots.txt` verification for ESPNcricinfo and Wisden. |
| **02. Commentary Live Scraping** | HalcyonVector (requests over Next.js JSON), Shrinath (BrightData JS), sst-cloud (Mock data). | **HalcyonVector** | **ADAPT HalcyonVector's heuristic**: Cricbuzz streaming Next.js payloads contain clean JSON in public HTML without requiring browser automation or API keys. Refactor into `src/adapters/cricbuzz_adapter.py`. |
| **03. Commentary Grammar Parsing** | ZainZoy (regex line grammar), HalcyonVector (Cricbuzz JSON), Paul-ans (RNN text prediction). | **ZainZoy** | **ADAPT ZainZoy's grammar**: Highly disciplined, unit-tested, deterministic regex grammar (`over.ball bowler to batter, desc`) preventing hallucinated numbers. Refactor into Pydantic models. |
| **04. Structured Match Analytics** | Anurag9557 (Polars), HalcyonVector (orjson + SQLite), vinaybale (DuckDB), ZainZoy (Pandas). | **Anurag9557** (Vectorized Polars) & **HalcyonVector** (Cricsheet orjson) | **REUSE Anurag9557's Polars pipeline**: Vectorized cumulative chase states (balls remaining, runs needed, required run rate, momentum windows) in Parquet format. Adapt HalcyonVector's 8-hex registry ID mapping. |
| **05. Scorecard Validation Gates** | ZainZoy (Module 14 validator), Anurag9557 (eval verifier). | **ZainZoy** & **Anurag9557** (Tie) | **REUSE / ADAPT both**: ZainZoy verifies arithmetic totals (batter runs + extras == total; wickets == dismissals); Anurag9557 verifies LLM claims against computed tree attributions. |
| **06. Entity Resolution & Nicknames** | ZainZoy (basic spaCy/rule-based), HalcyonVector (Cricsheet registry mapping). | **HalcyonVector** (baseline registry) | Existing projects only map exact names or Cricsheet IDs. **Must build our own Gazetteer Resolver** for journalistic nicknames ("King Kohli", "Boom Boom", ambiguous surname disambiguation). |
| **07. Sentiment Analysis** | princyhareshbhai (TextBlob), ZainZoy (VADER/DistilBERT), sst-cloud (Twitter API). | **ZainZoy** (VADER baseline) | **ADAPT ZainZoy's aspect-based baseline**: Distinguish bowler praise vs batting outcome ("devastating yorker"). TextBlob and Twitter APIs rejected. |
| **08. Topic Modeling & Clustering** | **None** of the 9 repositories implement topic modeling or clustering. | **NONE (Must build from scratch)** | Implement our comparative 4-model experimental matrix (TF-IDF vs. Sentence Transformers vs. HDBSCAN vs. BERTopic) under `src/clustering/`. |
| **09. Cross-Source Event Alignment** | **None** of the 9 repositories link news passages to match deliveries. | **NONE (Must build from scratch)** | **Core Original Contribution**: Implement hybrid linker (Entity Jaccard + Temporal Proximity + Vector Cosine + Event Keywords) linking articles to Cricsheet delivery sequences. |
| **10. Query Routing & Presentation** | SRIHARI18V (router), vinaybale (Next.js), Anurag9557 (FastAPI SSE). | **Anurag9557** (FastAPI) & **SRIHARI18V** (Router concept) | Build FastAPI service combining SRIHARI18V's routing concept with Anurag9557's clean API models and a modern React/Vite/Tailwind dashboard. |

---

## 3. Original Capabilities Not Covered by Any Existing Project

The audit confirms that merely merging existing repositories would **fail to solve the core research question**. None of the candidate projects address the integration of unstructured sports journalism with match evidence:

1. **Permitted News Ingestion & Body Extraction**:
   - None of the candidate projects collect long-form cricket articles, post-match reports, tactical essays, or editorial previews.
   - *Our Platform*: Implements automated sitemap/RSS discovery with Trafilatura body extraction, timezone canonicalization, and SHA-256 deduplication.

2. **Domain-Specific Entity Resolution with Disambiguation**:
   - Candidate projects rely either on exact string matching or static registry IDs. None resolve nicknames ("Hitman", "Boom Boom") or disambiguate identical surnames ("Sharma", "Curran") using co-occurring match context.
   - *Our Platform*: Implements a curated T20 World Cup Gazetteer with fuzzy Levenshtein matching and contextual squad disambiguation.

3. **Comparative Topic Discovery & Clustering Benchmarking**:
   - None of the 9 projects perform unsupervised topic modeling on cricket journalism or commentary.
   - *Our Platform*: Executes a controlled 4-model benchmark (TF-IDF + K-Means, Sentence Embeddings + K-Means, Sentence Embeddings + HDBSCAN, BERTopic) evaluated separately on news and commentary corpora.

4. **Media-to-Match Event Alignment Engine**:
   - None of the projects link an editorial sentence (e.g., "India lost three wickets in the powerplay before Kohli rebuilt") to the exact Cricsheet delivery window (Overs 0.1–5.6).
   - *Our Platform*: Implements the hybrid alignment algorithm scoring entity overlap, temporal proximity, and semantic similarity to ground media claims in delivery evidence.

5. **Attention vs. Performance Index ($APR$)**:
   - None of the projects evaluate media narrative bias relative to objective player performance.
   - *Our Platform*: Quantifies the ratio between media attention share and objective statistical impact.

6. **Interactive Evidence Inspector & Provenance Backpointers**:
   - None of the dashboards allow a user to click a discovered topic or summary and inspect the exact underlying raw paragraph and verified Cricsheet ball-by-ball record.
   - *Our Platform*: Provides clickable provenance tracing down to the raw archive payload and delivery ID.
