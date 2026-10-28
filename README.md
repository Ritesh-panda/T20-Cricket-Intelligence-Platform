# T20 Cricket Intelligence Platform
### Open-Source Sports Intelligence, Narrative Discovery & Event Grounding for T20 Cricket

[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646cff.svg)](https://vitejs.dev/)
[![SQLite WAL](https://img.shields.io/badge/SQLite-WAL%20Mode-003B57.svg)](https://www.sqlite.org/)
[![Pytest 112/112](https://img.shields.io/badge/pytest-112%20passed%20(100%25)-brightgreen.svg)](https://docs.pytest.org/)
[![Vitest 9/9](https://img.shields.io/badge/vitest-9%20passed%20(100%25)-brightgreen.svg)](https://vitest.dev/)
[![License: ODC-By & CC BY-SA](https://img.shields.io/badge/License-ODC--By%20%2B%20CC%20BY--SA%204.0-lightgrey.svg)](LICENSE)

An end-to-end sports intelligence and NLP research system that bridges the gap between **unstructured cricket media (news articles, editorial tournament reports, expert analyses)** and **structured match facts (ball-by-ball deliveries, wickets, and match phases from Cricsheet)**.

The platform introduces the **Attention-to-Performance Discrepancy Index (APDI)**, a mathematically rigorous framework quantifying the divergence between editorial media attention prominence and objective on-field athletic output across role cohorts (Batters, Bowlers, Teams).

---

## 📑 Table of Contents

1. [System Architecture](#-system-architecture)
   - [1.1 High-Level End-to-End Architecture](#11-high-level-end-to-end-architecture)
   - [1.2 Ingestion & Provenance Lifecycle Flow](#12-ingestion--provenance-lifecycle-flow)
   - [1.3 Cricket NLP & Entity Resolution Pipeline](#13-cricket-nlp--entity-resolution-pipeline)
   - [1.4 Attention-to-Performance Discrepancy Index (APDI) Architecture](#14-attention-to-performance-discrepancy-index-apdi-architecture)
   - [1.5 Database Schema & Entity Relationship Model](#15-database-schema--entity-relationship-model)
   - [1.6 Full-Stack Application Component Hierarchy](#16-full-stack-application-component-hierarchy)
   - [1.7 CLI Pipeline & Automation Workflow](#17-cli-pipeline--automation-workflow)
2. [Key Verified Metrics](#-key-verified-metrics-icc-mens-t20-world-cup-2024)
3. [Quickstart: Running Locally](#-quickstart-running-locally)
   - [Step 1: Clone Repository & Virtual Environment](#step-1-clone-repository--virtual-environment)
   - [Step 2: Backend Setup & API Launch](#step-2-backend-setup--api-launch)
   - [Step 3: Frontend Dashboard Launch](#step-3-frontend-dashboard-launch)
4. [Running the Autonomous Pipeline](#-running-the-autonomous-pipeline)
5. [Testing & Quality Assurance](#-testing--quality-assurance)
6. [Essential Guides & Documentation](#-essential-guides--documentation)
7. [License & Ethical Compliance](#-license--ethical-compliance)

---

## 🏛️ System Architecture

### 1.1 High-Level End-to-End Architecture

```mermaid
flowchart TD
    subgraph S01["01. Open Data Sources"]
        CS["Cricsheet Open Data\n(Ball-by-Ball JSON / ODC-By 1.0)"]
        WM["Wikimedia Foundation\n(Editorial Tournament Reports / CC BY-SA 4.0)"]
        SQUAD["Official Squad Rosters\n(Player Profiles, Bat/Bowl Styles)"]
    end

    subgraph S02["02. Ingestion & Validation Engine"]
        AD_C["Cricsheet Adapter\n(10 Fixtures, 2,314 Deliveries)"]
        AD_N["Wikimedia Adapter\n(Trafilatura HTML Extractor)"]
        SHA["Provenance Auditor\n(SHA-256 Content Hashing & Deduplication)"]
        VAL["Pydantic v2 Schema Gate\n(Zero Missing/Fabricated Invariants)"]
    end

    subgraph S03["03. Canonical Storage Layer"]
        DB[("SQLite 3 Database\n(data/cricket_intel.db, WAL Mode, Schema v5)")]
        PROV[("Provenance & Ingestion Log\n(source_records, ingestion_runs)")]
    end

    subgraph S04["04. Cricket NLP & Sentiment Engine"]
        TOK["Cricket Regex Tokenizer\n(Overs 19.4, Scores 176/7, Acronyms)"]
        GAZ["Gazetteer Boundary Matcher\n(Longest-Phrase Priority)"]
        ER["Cross-Entity Linker & Alias Resolver\n(Cricsheet IDs ↔ Gazetteer Slugs)"]
        SENT["Aspect-Based Sentiment Engine\n(Batter vs Bowler Framing Rules)"]
        CLUST["Topic Clustering Engine\n(Sentence-Transformers + KMeans k=3)"]
    end

    subgraph S05["06. Analytics & Discrepancy Engine (APDI)"]
        PERF["Performance Calculator\n(Runs, SR, Wickets, Economy, Phases)"]
        ATTN["Attention Calculator\n(Mentions, Reach, Publisher Diversity, Prominence)"]
        GATE["Minimum Cohort & Sample Gate\n(Strict NULL for Insufficient Data)"]
        APDI["APDI Formulation Engine\n(NormAttention - NormPerformance)"]
    end

    subgraph S06["07. Serving & Presentation Layer"]
        API["FastAPI REST Backend (:8000)\n(OpenAPI Docs, Pagination, Health Probes)"]
        UI["React 18 + Vite Dashboard (:5173)\n(APDI Explorer, Scorecards, Player Profiles)"]
    end

    CS --> AD_C --> SHA --> VAL --> DB
    WM --> AD_N --> SHA --> VAL --> DB
    SQUAD --> AD_C
    VAL --> PROV

    DB --> TOK --> GAZ --> ER --> SENT --> DB
    DB --> CLUST --> DB

    DB --> PERF --> GATE
    DB --> ATTN --> GATE
    GATE --> APDI --> DB

    DB --> API
    API --> UI
```

---

### 1.2 Ingestion & Provenance Lifecycle Flow

Every document and match ingested by the platform receives an immutable SHA-256 cryptographic provenance record before persisting to the database.

```mermaid
sequenceDiagram
    autonumber
    participant SRC as External Data Source
    participant INGEST as Ingestion Pipeline
    participant SHA as SHA-256 Content Auditor
    participant SCHEMA as Pydantic Schema Validator
    participant DB as SQLite Storage Manager (WAL)
    participant RUN as Ingestion Run Auditor

    INGEST->>SRC: Discover & Fetch Raw Asset (JSON / HTML)
    SRC-->>INGEST: Raw Response Payload
    INGEST->>SHA: Compute SHA-256 Hash of Raw Content
    SHA->>DB: Check if Content Hash Exists (source_records)
    alt Hash Already Present (Idempotent Skip)
        DB-->>INGEST: Duplicate Detected -> Log SKIPPED
    else Fresh or Updated Content
        INGEST->>SCHEMA: Validate Payload Against Canonical Schema
        SCHEMA-->>INGEST: Validated Domain Objects
        INGEST->>DB: Insert Canonical Record (Match / Article / Delivery)
        INGEST->>DB: Record Immutable Provenance (source_records)
    end
    INGEST->>RUN: Commit Batch Audit Metrics (records_ingested, skipped, errors)
    RUN->>DB: Persist Execution Run to ingestion_runs Table
```

---

### 1.3 Cricket NLP & Entity Resolution Pipeline

The platform utilizes a cricket-specialized Natural Language Processing pipeline that respects sports-specific numeric formats, boundary rules, and entity aliases.

```mermaid
flowchart LR
    RAW["Raw Editorial Text\n(HTML / RSS Articles)"] --> CLEAN["Text Cleaner\n• HTML Unescape\n• Boilerplate Strip\n• Unicode Normalization"]
    
    CLEAN --> TOK["Cricket Tokenizer\n• Overs (19.4)\n• Scores (176/7)\n• Acronyms (IND, SA)"]
    
    TOK --> GAZ["Gazetteer Matcher\n• Boundary Anchoring\n• Longest-Phrase Priority\n• Substring Guard"]
    
    GAZ --> ER["Entity Disambiguator\n• Context Linker\n• Alias Canonicalization\n• Ambiguity Flagging"]
    
    ER --> MENT[("entity_mentions\n(Resolved IDs,\nCharacter Spans)")]
    
    MENT --> SENT["Aspect Sentiment Engine\n• Negation Windowing\n• Batter vs Bowler Context\n• Domain Lexicons"]
    
    SENT --> FRAME[("sentiment_baselines\n(Framing Scores,\nPublisher Breakdown)")]
```

---

### 1.4 Attention-to-Performance Discrepancy Index (APDI) Architecture

The APDI formula mathematically measures divergence between editorial media attention and objective athletic performance across standardized role cohorts (Batters, Bowlers, Teams).

```mermaid
flowchart TD
    subgraph PerfTrack["Objective Match Performance"]
        DELIV[("Ball-by-Ball Deliveries\n(2,314 Records)")] --> CALC_P["Compute Raw Performance Composite\n• Batting: Runs, Strike Rate, 4s, 6s, Average\n• Bowling: Economy, Wickets, Maidens, Strike Rate\n• Team: Win %, Run Rate, Margin"]
        CALC_P --> COHORT_P["Partition into Role Cohorts\n(Batters / Bowlers / Teams)"]
        COHORT_P --> RANK_P["Compute Percentile Rank\nNormPerf = Rank / (N - 1) ∈ [0.0, 1.0]"]
    end

    subgraph AttnTrack["Editorial Media Visibility"]
        TEXT[("Editorial Corpus\n(Articles & Paragraphs)")] --> CALC_A["Compute Raw Media Attention Composite\n• Mention Volume (Paragraphs vs Raw)\n• Article Reach & Publisher Diversity\n• Position Prominence (Headline=3.0, Lead=1.5, Body=1.0)"]
        CALC_A --> COHORT_A["Partition into Role Cohorts\n(Batters / Bowlers / Teams)"]
        COHORT_A --> RANK_A["Compute Percentile Rank\nNormAttn = Rank / (N - 1) ∈ [0.0, 1.0]"]
    end

    subgraph QualityGate["Evidence Sufficiency & Eligibility Gate"]
        SAMPLE{"Sufficient Sample Size?\n• Cohort Size N ≥ 5\n• Batter Balls ≥ 10\n• Bowler Overs ≥ 2.0\n• Team Matches ≥ 1"}
    end

    RANK_P --> SAMPLE
    RANK_A --> SAMPLE

    SAMPLE -- "NO" --> INSUF["INSUFFICIENT_DATA\n• APDI = NULL (Strict Zero-Fabrication)\n• Category = INSUFFICIENT_DATA\n• Retain Sample Indicators & Warnings"]
    SAMPLE -- "YES" --> FORMULA["APDI Formulation\nAPDI = NormAttn - NormPerf ∈ [-1.0, +1.0]"]

    FORMULA --> CLASSIFY{"Discrepancy Category Threshold\n(Threshold = 0.20)"}
    CLASSIFY -- "APDI > +0.20" --> OVER["OVER_ATTENDED\n(Attention outstrips performance)"]
    CLASSIFY -- "APDI < -0.20" --> UNDER["UNDER_ATTENDED\n(Performance outstrips attention)"]
    CLASSIFY -- "-0.20 ≤ APDI ≤ +0.20" --> BAL["BALANCED\n(Attention aligns with performance)"]

    INSUF --> PERSIST[("Persist to apdi_records Table")]
    OVER --> PERSIST
    UNDER --> PERSIST
    BAL --> PERSIST
```

---

### 1.5 Database Schema & Entity Relationship Model

The underlying SQLite database (`data/cricket_intel.db`, Schema Version 5) strictly enforces foreign-key relationships, transactional guarantees, and WAL mode.

```mermaid
erDiagram
    teams ||--o{ matches : "team1_id / team2_id"
    teams ||--o{ players : "primary_team_id"
    matches ||--o{ deliveries : "match_id"
    players ||--o{ deliveries : "batter_id / bowler_id"
    source_records ||--o{ matches : "provenance_id"
    source_records ||--o{ articles : "provenance_id"
    articles ||--o{ article_paragraphs : "article_id"
    article_paragraphs ||--o{ entity_mentions : "paragraph_id"
    players ||--o{ performance_metrics : "entity_id"
    players ||--o{ attention_metrics : "entity_id"
    players ||--o{ apdi_records : "entity_id"
    analytics_runs ||--o{ apdi_records : "run_id"

    matches {
        text match_id PK
        text tournament
        text match_date
        text venue
        text team1_id FK
        text team2_id FK
        text winner_id
        text provenance_id FK
    }

    deliveries {
        text delivery_id PK
        text match_id FK
        integer innings
        integer over_num
        integer ball_num
        text batter_id FK
        text bowler_id FK
        integer batter_runs
        integer extra_runs
        integer total_runs
        boolean is_wicket
        text wicket_kind
        text phase
    }

    players {
        text player_id PK
        text full_name
        text cricsheet_id
        text primary_team_id FK
        text batting_style
        text bowling_style
        text aliases_json
    }

    teams {
        text team_id PK
        text name
        text code
        text aliases_json
    }

    source_records {
        text provenance_id PK
        text source_name
        text source_url
        text content_hash_sha256
        text license_tag
        boolean redistributable
    }

    articles {
        text article_id PK
        text title
        text url
        text source_domain
        text published_date
        text provenance_id FK
    }

    article_paragraphs {
        text paragraph_id PK
        text article_id FK
        integer paragraph_index
        text text
        text section_type
    }

    entity_mentions {
        text mention_id PK
        text paragraph_id FK
        text surface_text
        text entity_type
        text resolved_id
        text resolution_status
    }

    performance_metrics {
        text metric_id PK
        text entity_id FK
        text role
        text tournament
        integer matches_played
        integer runs_scored
        real strike_rate
        integer wickets_taken
        real bowling_economy
        real raw_performance_composite
    }

    attention_metrics {
        text metric_id PK
        text entity_id FK
        text tournament
        integer paragraph_count
        integer raw_mention_count
        integer article_reach
        integer source_diversity_count
        real prominence_score
        real raw_attention_composite
    }

    apdi_records {
        text record_id PK
        text run_id FK
        text entity_id FK
        text entity_name
        text role_cohort
        real raw_attention_score
        real normalized_attention_score
        real raw_performance_score
        real normalized_performance_score
        real apdi_value
        text discrepancy_category
        text evidence_sufficiency_status
    }

    analytics_runs {
        text run_id PK
        text tournament
        text status
        integer entities_processed
        integer valid_apdi_count
        integer insufficient_data_count
        text completed_at_utc
    }
```

---

### 1.6 Full-Stack Application Component Hierarchy

The platform provides a dual-surface architecture: a high-throughput FastAPI REST API serving typed JSON contracts, and a responsive React 18 / Vite single-page dashboard.

```mermaid
flowchart TB
    subgraph Browser["User Browser (:5173)"]
        SHELL["App Shell & Navigation Sidebar\n(Header, Theme Toggle, Active Tournament Scope)"]
        
        subgraph Views["Dashboard Application Views"]
            V1["Overview Dashboard\n(KPI Cards, Pipeline Status, Attention BarCharts, Health)"]
            V2["Matches Explorer & Scorecard\n(Fixture List, Innings Aggregates, Batting & Bowling Scorecards)"]
            V3["Player Directory & Research Profile\n(Interactive Table, Full Names, Bat/Bowl Styles, Rich Profile)"]
            V4["APDI Discrepancy Explorer\n(Mathematical Matrix, Cohort Filters, Discrepancy Badges)"]
            V5["Media Intelligence & Articles\n(Editorial Harvest Corpus, Paragraph Splitter, Entity Offsets)"]
            V6["Topics & Narratives\n(KMeans Cluster Clouds, Dominant Themes, Keyword Distributions)"]
            V7["System Health & Observability\n(4-Tier Audit: Liveness, Storage, Corpus, APDI Invariants)"]
            V8["Provenance & Data Sources\n(Immutable SHA-256 Catalog, Ingestion Audit Runs, Licensure)"]
        end

        SHELL --> V1
        SHELL --> V2
        SHELL --> V3
        SHELL --> V4
        SHELL --> V5
        SHELL --> V6
        SHELL --> V7
        SHELL --> V8
    end

    subgraph ClientLib["Frontend API Client (frontend/src/lib/api.ts)"]
        RQ["TanStack React Query\n(Caching, Invalidation, Error Boundaries)"]
        AXIOS["Axios HTTP Client\n(Base URL: http://127.0.0.1:8000, 15s Timeout)"]
        RQ --> AXIOS
    end

    Views --> RQ

    subgraph BackendAPI["FastAPI REST Application (src/api/main.py :8000)"]
        CORS["CORS Middleware\n(Strict Origin Whitelist)"]
        LIFE["Lifespan Context Manager\n(SQLite Persistence Binding)"]
        ERR["Standardized Error Handlers\n(400, 404, 422, 500 JSON Envelopes)"]
        
        subgraph Routers["API v1 Route Controllers"]
            R_HEALTH["/health & /ready"]
            R_MATCH["/api/v1/matches & /performance"]
            R_PLAY["/api/v1/players & /api/v1/teams"]
            R_ART["/api/v1/articles & /paragraphs"]
            R_NLP["/api/v1/topics & /entities"]
            R_ANLY["/api/v1/analytics/overview & /attention & /performance & /apdi"]
            R_OBS["/api/v1/observability/pipeline-stats & /sources & /analytics-runs"]
        end

        CORS --> Routers
        LIFE --> Routers
        ERR --> Routers
    end

    AXIOS -->|HTTP JSON Requests| CORS
```

---

### 1.7 CLI Pipeline & Automation Workflow

The platform provides a modular CLI interface (`python -m src.pipeline.cli`) capable of running isolated subtasks or executing the complete automated cascade.

```mermaid
flowchart TD
    START(["Run: python -m src.pipeline.cli run"]) --> STEP1["1. Ingestion & Adapters\n• Ingest Cricsheet Matches & Deliveries\n• Ingest Editorial Tournament Articles"]
    STEP1 --> STEP2["2. Text Processing & NLP\n• Extract Paragraphs & Strip Boilerplate\n• Cricket Tokenization & Entity Extraction\n• Aspect-Based Sentiment Framing"]
    STEP2 --> STEP3["3. Topic Clustering\n• Dense Sentence Embeddings\n• KMeans Topic Clustering (k=3)"]
    STEP3 --> STEP4["4. Objective Performance\n• Aggregate Deliveries by Batter, Bowler, Team\n• Compute Raw Performance Composites"]
    STEP4 --> STEP5["5. Media Attention Calculation\n• Aggregate Mentions, Reach, Prominence\n• Compute Raw Attention Composites"]
    STEP5 --> STEP6["6. APDI Calculation Engine\n• Resolve Cross-Entity Aliases\n• Evaluate Minimum Sample Gates\n• Compute APDI & Classify Discrepancy"]
    STEP6 --> STEP7["7. Player Metadata Enrichment\n• Align Full Names, Batting & Bowling Styles"]
    STEP7 --> STEP8["8. Analytical Summary Report\n• Display Final Terminal Metrics & Invariant Checks"]
    STEP8 --> END(["Pipeline Completed Successfully [Zero Errors]"])
```

---

## 📊 Key Verified Metrics (ICC Men's T20 World Cup 2024)

| Entity / Dimension | Verified Benchmark Count | Integrity & Verification Method |
| :--- | :---: | :--- |
| **Tournament Fixtures** | **10 Matches** | 100% exact parity with raw Cricsheet JSON; verified in `validate_raw_matches_against_db.py`. |
| **Ball-by-Ball Records** | **2,314 Deliveries** | Complete delivery facts: runs, extras, wickets, bowler/batter assignments, overs, and phases. |
| **Player Registry** | **107 Players** | Canonical identities enriched with batting styles, bowling styles, Cricsheet IDs, and aliases. |
| **Team Registry** | **9 Teams** | Canonical international squads (`IND`, `SA`, `AUS`, `ENG`, `PAK`, `CAN`, `BAN`, `UNI`, `AFG`). |
| **Editorial Documents** | **5 Articles** | Harvested from Wikimedia Foundation under CC BY-SA 4.0; 314 structured paragraphs. |
| **Entity Mentions** | **683 Mentions** | Disambiguated and bound to canonical player/team IDs using longest-phrase gazetteer matching. |
| **Topic Clusters** | **3 Clusters** | Identified via Sentence Transformers + KMeans ($k=3$): Rivalry History, Match Events, Rosters. |
| **Performance Evaluated** | **162 Cohorts** | Objective batting, bowling, and team performance metrics calculated strictly from deliveries. |
| **Attention Evaluated** | **23 Entities** | Granular prominence, article reach, and publisher diversity computed across media passages. |
| **APDI Evaluations** | **116 Total** | **13 Valid classified** (7 Balanced, 3 Over-Attended, 3 Under-Attended) + **103 Preserved NULL** (`INSUFFICIENT_DATA`). |
| **Test Suite Coverage** | **121 / 121 Tests** | **112 backend tests** (`pytest`) + **9 frontend tests** (`vitest`) + 0 TypeScript errors. |

---

## ⚡ Quickstart: Running Locally

Follow these instructions to set up and launch the entire platform from scratch on any machine.

### Step 1: Clone Repository & Virtual Environment

```bash
# Clone the repository
git clone https://github.com/Ritesh-panda/T20-Cricket-Intelligence-Platform.git
cd T20-Cricket-Intelligence-Platform

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate
```

### Step 2: Backend Setup & API Launch

```bash
# Install all required Python dependencies
pip install -r requirements.txt

# Start the FastAPI backend server (runs on http://127.0.0.1:8000)
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

> **Interactive API Documentation:** Open your browser and navigate to **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** for interactive Swagger UI docs.

### Step 3: Frontend Dashboard Launch

In a new terminal window:

```bash
# Navigate to the frontend directory
cd frontend

# Install frontend npm dependencies
npm install

# Start the Vite development server (runs on http://127.0.0.1:5173)
npm run dev
```

> **Live Dashboard:** Open your browser and navigate to **[http://127.0.0.1:5173/](http://127.0.0.1:5173/)** to access the research dashboard.

---

## 🚀 Running the Autonomous Pipeline

The repository includes a ready-to-run benchmark database (`data/cricket_intel.db`). If you wish to re-execute any stage or the entire pipeline end-to-end, use the CLI commands:

```bash
# Execute the entire intelligence cascade end-to-end
python -m src.pipeline.cli run

# Or execute individual pipeline stages independently:

# 1. Harvest & ingest raw tournament fixtures and editorial articles
python -m src.pipeline.cli ingest

# 2. Extract paragraphs, tokenize, and perform entity resolution & sentiment
python -m src.pipeline.cli process-text

# 3. Discover topic clusters and keyword groupings
python -m src.pipeline.cli cluster-topics --k 3

# 4. Compute objective player and team performance from deliveries
python -m src.pipeline.cli compute-performance

# 5. Compute editorial media attention and prominence scores
python -m src.pipeline.cli compute-attention

# 6. Compute Attention-to-Performance Discrepancy Index (APDI)
python -m src.pipeline.cli compute-apdi --tournament "ICC Men's T20 World Cup"

# 7. Print comprehensive terminal intelligence report
python -m src.pipeline.cli report
```

---

## 🧪 Testing & Quality Assurance

The codebase includes an exhaustive automated test suite validating every tier of the application:

```bash
# 1. Run all backend tests (112 tests covering Ingestion, NLP, Analytics, API, and Storage)
pytest -v

# 2. Run frontend unit and integration tests (9 tests)
cd frontend
npm run test

# 3. Run frontend TypeScript type safety check (0 errors)
npm run typecheck

# 4. Build frontend production distribution bundle
npm run build
cd ..

# 5. Run raw-match ball-by-ball parity validation script
python scripts/validate_raw_matches_against_db.py

# 6. Run APDI threshold sensitivity analysis
python scripts/phase9_apdi_sensitivity.py

# 7. Run NLP gold-standard evaluation benchmark
python scripts/evaluate_nlp_gold_set.py
```

---

## 📚 Essential Guides & Documentation

- 📖 **[USER_GUIDE.md](docs/USER_GUIDE.md)**: **Complete User Manual** covering setup, UI walkthrough (Scorecards, Player Profiles, APDI Explorer, Observability), API reference, and APDI interpretation.
- 🧪 **[TESTING_AND_QA_GUIDE.md](docs/TESTING_AND_QA_GUIDE.md)**: **Complete Tester's Specification & Function Guide** detailing test execution, function-by-function testing reference, invariants, edge cases, and QA acceptance checklists.
- 📐 **[PHASE_9_APDI_METHODOLOGY.md](docs/PHASE_9_APDI_METHODOLOGY.md)**: In-depth mathematical formulation, ranking properties, and numerical sensitivity analysis of the APDI metric.
- ⚖️ **[PHASE_9_SOURCE_LEGALITY_AUDIT.md](docs/PHASE_9_SOURCE_LEGALITY_AUDIT.md)**: Exhaustive compliance audit of all data sources across 11 legal dimensions.
- 📋 **[PHASE_9_RELEASE_CHECKLIST.md](docs/PHASE_9_RELEASE_CHECKLIST.md)**: Item-by-item release verification and research integrity sign-offs.

---

## 📜 License & Ethical Compliance

- **Structured Cricket Data**: Provided by [Cricsheet](https://cricsheet.org/) under the [Open Data Commons Attribution License (ODC-By 1.0)](https://opendatacommons.org/licenses/by/1-0/).
- **Editorial Summaries**: Sourced from [Wikipedia / Wikimedia Foundation](https://en.wikipedia.org/) under [Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).
- **Ethical Web Scraping Protocol**: The platform adheres strictly to `robots.txt` directives and rate limits. Commercial publishers with restrictive terms (ESPNcricinfo, Cricbuzz, Wisden) are categorized as `RESTRICTED` and withheld from automated web harvesting.
