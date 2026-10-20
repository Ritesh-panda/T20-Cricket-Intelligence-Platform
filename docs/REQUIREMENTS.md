# Requirements Specification: T20 Cricket Intelligence Platform

## 1. Introduction & Scope

This document specifies the functional, non-functional, and data requirements for the T20 Cricket Intelligence Platform. The system collects, standardizes, enriches, and correlates unstructured cricket journalism and written commentary with structured match event data from the ICC Men's T20 World Cup tournaments.

---

## 2. Functional Requirements (FR)

### Module A: Source Registry & Adapter Framework
- **FR-A.1 Configuration-Driven Adapters**: The system MUST support pluggable source adapters configured via declarative YAML/JSON schemas (specifying URL patterns, rate limits, headers, parser rules).
- **FR-A.2 Permitted Ingestion Verification**: Prior to scraping any domain, the adapter MUST verify `robots.txt` compliance and disallow crawling paths flagged with `Disallow`.
- **FR-A.3 Open Dataset Ingestion**: The system MUST provide native adapters for Cricsheet match data (YAML/JSON/CSV) to ingest ball-by-ball facts without network scraping overhead.

### Module B: Crawling, Ingestion & Discovery
- **FR-B.1 Politeness & Rate Limiting**: The crawling engine MUST enforce configurable per-domain request rates (default <= 0.5 req/sec) using a token-bucket or leaky-bucket rate limiter.
- **FR-B.2 Idempotent Checkpointing**: The ingestion pipeline MUST record ingested URLs and content hashes in a persistent state store. Re-running the pipeline MUST skip previously processed documents without re-downloading or re-processing.
- **FR-B.3 Robust Retries & Backoff**: Network requests MUST implement exponential backoff with jitter (max 3 retries) for transient 429/5xx HTTP errors.
- **FR-B.4 Strict Access Limits**: The crawler MUST NOT attempt to bypass paywalls, solve CAPTCHAs, or spoof credentials.

### Module C: Article & Commentary Extraction
- **FR-C.1 Main Text Extraction**: Ingestion of news HTML MUST isolate the primary article body, headline, author, publication timestamp (UTC), and tags using Trafilatura or robust fallback DOM extractors, eliminating navigation bars, sidebars, and ads.
- **FR-C.2 Ball-by-Ball Commentary Parsing**: Commentary feeds/pages MUST be parsed into discrete delivery records specifying over number, ball number, batter, bowler, outcome, and raw commentary text.
- **FR-C.3 Language Filtering**: The system MUST support English-language text and detect/flag non-English entries.

### Module D: Canonical Data Modeling, Validation & Deduplication
- **FR-D.1 Pydantic Schema Validation**: All ingested raw records MUST be validated against strict Pydantic v2 schemas at module boundaries.
- **FR-D.2 Content Deduplication**: Articles and commentary records MUST generate deterministic content hashes (SHA-256 over normalized text). Duplicate articles (e.g., syndicated wire reports across publishers) MUST be grouped with primary canonical reference.
- **FR-D.3 Timezone Normalization**: All timestamps MUST be converted and stored in ISO 8601 UTC format.

### Module E: Storage & Provenance
- **FR-E.1 Multi-Tier Storage**:
  - *Tier 1 (Raw Archive)*: Immutable raw JSONL/HTML snapshots stored with timestamp and provenance metadata.
  - *Tier 2 (Relational/Tabular)*: Canonical entities (matches, teams, players, deliveries, articles) stored in PostgreSQL / SQLite.
  - *Tier 3 (Reproducible Datasets)*: Exportable Parquet datasets for ML/NLP modeling.
- **FR-E.2 Lineage Tracking**: Every derived record (entity, sentiment score, embedding, cluster assignment, event link) MUST retain foreign keys referencing the exact raw document ID, pipeline version, and model checkpoint.

### Module F: Cricket Named Entity Recognition (NER) & Resolution
- **FR-F.1 Cricket Entity Extraction**: The system MUST extract entities in four categories: `PLAYER`, `TEAM`, `VENUE`, and `TOURNAMENT_PHASE` (e.g., "Powerplay", "Death Overs", "Super Over").
- **FR-F.2 Entity Resolution & Alias Mapping**: The system MUST resolve name variants, nicknames, and abbreviations (e.g., "Virat Kohli", "V. Kohli", "King Kohli", "Kohli") to a unique canonical Player ID using a curated cricket player gazetteer with fuzzy matching and confidence thresholds.
- **FR-F.3 Disambiguation by Match Context**: If an ambiguous surname is detected (e.g., "Sharma" -> Rohit Sharma vs. Mohit Sharma), the resolver MUST use co-occurring team names, match dates, or squad lists to disambiguate.

### Module G: Sentiment Analysis & Text Enrichment
- **FR-G.1 Multi-Level Sentiment**: The system MUST compute sentiment scores at both document level (overall tone of article) and entity/aspect level (sentiment toward specific player/team).
- **FR-G.2 Cricket-Context Awareness**: The sentiment engine MUST distinguish subjective author tone from objective match events (e.g., a bowler taking a wicket generates negative sentiment for the batting team but positive for the bowling team; "devastating yorker" is positive for the bowler).
- **FR-G.3 Dense Vector Embeddings**: Generate normalized semantic embeddings for article passages and commentary snippets using a local transformer model (e.g., `sentence-transformers/all-MiniLM-L6-v2`).

### Module H: Clustering & Topic Modeling
- **FR-H.1 Multi-Algorithm Benchmarking**: The system MUST execute and log comparative experiments across:
  - Baseline 1: TF-IDF + K-Means
  - Baseline 2: Sentence Embeddings + K-Means
  - Experiment 3: Sentence Embeddings + HDBSCAN (outlier-aware)
  - Experiment 4: BERTopic (c-TF-IDF topic representations)
- **FR-H.2 Separate Corpus Evaluation**: News articles and ball-by-ball commentary MUST be evaluated in separate clustering runs before any joint cross-corpus clustering is attempted.
- **FR-H.3 Explainable Cluster Representations**: For every discovered cluster, the system MUST compute top keyword descriptors, representative documents, and centroid distance metrics.

### Module I: Match Analytics & Cross-Source Event Alignment
- **FR-I.1 Delivery-Level Match Metrics**: Compute structured statistics from Cricsheet data: Phase run rates (Overs 1-6, 7-15, 16-20), wicket clusters, dot-ball percentages, and leverage/pressure points.
- **FR-I.2 Media-to-Match Event Linker**: Match article paragraphs and commentary narratives to structured match events using:
  1. Temporal constraints (match date ± 48 hours for reports; match in-progress for commentary).
  2. Co-occurring resolved player and team entities.
  3. Delivery-sequence feature matching (e.g., mentions of "hat-trick", "19th over", "50 off 24").
  4. Vector semantic similarity between paragraph and commentary window.
- **FR-I.3 Link Scoring & Confidence**: Every link MUST output an evidence score (0.0 to 1.0) and human-readable explanation of why the link was established.
- **FR-I.4 Attention vs. Performance Index**: Calculate the ratio between player media mentions/sentiment and objective match impact scores (e.g., runs, wickets, MVP points).

### Module J: Evaluation & Experiment Tracking
- **FR-J.1 Automated Experiment Logging**: Every clustering and alignment run MUST log parameters, random seeds, execution duration, and evaluation metrics to a structured JSON/MLflow-compatible log.
- **FR-J.2 Gold-Standard Benchmarking**: The system MUST evaluate NER, sentiment, clustering, and event alignment against manually verified ground-truth test sets.

### Module K: API & Dashboard
- **FR-K.1 REST API**: FastAPI backend providing read endpoints for tournaments, matches, players, discovered topics, article clusters, and linked match events.
- **FR-K.2 Interactive Visualizations**: Web dashboard featuring:
  - Tournament Overview & Ingestion Health.
  - Interactive Topic Explorer (2D UMAP scatter, top words, representative articles).
  - Match Intelligence & Timeline (delivery-by-delivery timeline mapped to contemporaneous commentary and post-match articles).
  - Player/Team Media Attention vs. Performance radar/scatter charts.
- **FR-K.3 Provenance Inspector**: User interface allowing any insight or chart element to be clicked to inspect source article snippets and raw Cricsheet delivery records.

### Module L: Tests, Observability & Deployment
- **FR-L.1 Test Coverage**: Pytest test suite covering unit tests for adapters, schemas, entity resolution, and alignment scoring, plus end-to-end integration tests on synthetic fixture data.
- **FR-L.2 Structured Logging**: Python `logging` or `loguru` outputting JSON logs with timestamps, module names, and error stack traces.

---

## 3. Non-Functional Requirements (NFR)

- **NFR-1 Local-First Execution**: The system MUST run entirely on a standard modern PC (16GB RAM, multi-core CPU) without requiring paid third-party APIs, GPU clusters, or cloud services.
- **NFR-2 Determinism & Reproducibility**: Given the same seed, datasets, and configurations, clustering and embedding pipelines MUST produce identical cluster assignments or deterministic metric outputs.
- **NFR-3 Storage Efficiency**: Cleaned datasets MUST be stored in columnar Parquet or compressed JSONL, keeping storage footprint within a few gigabytes for an entire tournament.
- **NFR-4 Security & Credential Hygiene**: No credentials, API tokens, or personal identifiers may be hardcoded. All settings must be sourced from `.env` via Pydantic Settings.
- **NFR-5 Graceful Degradation**: If an external network adapter fails or is rate-limited, the system MUST log a clear warning, isolate the failure, and allow offline analysis of previously ingested data.
- **NFR-6 Modularity & Loose Coupling**: Components MUST communicate only via standard Python interfaces and canonical data models; replacing an adapter or ML model must require zero modifications to unrelated modules.
