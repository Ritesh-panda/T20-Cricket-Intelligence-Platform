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
        CS["Cricsheet Open Data<br/>(Ball-by-Ball JSON / ODC-By 1.0)"]
        WM["Wikimedia Foundation<br/>(Editorial Tournament Reports / CC BY-SA 4.0)"]
        SQUAD["Official Squad Rosters<br/>(Player Profiles, Bat/Bowl Styles)"]
    end

    subgraph S02["02. Ingestion and Validation Engine"]
        AD_C["Cricsheet Adapter<br/>(10 Fixtures, 2,314 Deliveries)"]
        AD_N["Wikimedia Adapter<br/>(Trafilatura HTML Extractor)"]
        SHA["Provenance Auditor<br/>(SHA-256 Content Hashing and Deduplication)"]
        VAL["Pydantic v2 Schema Gate<br/>(Zero Missing/Fabricated Invariants)"]
    end

    subgraph S03["03. Canonical Storage Layer"]
        DB["SQLite 3 Database<br/>(data/cricket_intel.db, WAL Mode, Schema v5)"]
        PROV["Provenance and Ingestion Log<br/>(source_records, ingestion_runs)"]
    end

    subgraph S04["04. Cricket NLP and Sentiment Engine"]
        TOK["Cricket Regex Tokenizer<br/>(Overs 19.4, Scores 176/7, Acronyms)"]
        GAZ["Gazetteer Boundary Matcher<br/>(Longest-Phrase Priority)"]
        ER["Cross-Entity Linker and Alias Resolver<br/>(Cricsheet IDs to Gazetteer Slugs)"]
        SENT["Aspect-Based Sentiment Engine<br/>(Batter vs Bowler Framing Rules)"]
        CLUST["Topic Clustering Engine<br/>(Sentence-Transformers + KMeans k=3)"]
    end

    subgraph S05["05. Analytics and Discrepancy Engine (APDI)"]
        PERF["Performance Calculator<br/>(Runs, SR, Wickets, Economy, Phases)"]
        ATTN["Attention Calculator<br/>(Mentions, Reach, Publisher Diversity, Prominence)"]
        GATE["Minimum Cohort and Sample Gate<br/>(Strict NULL for Insufficient Data)"]
        APDI["APDI Formulation Engine<br/>(NormAttention - NormPerformance)"]
    end

    subgraph S06["06. Serving and Presentation Layer"]
        API["FastAPI REST Backend - Port 8000<br/>(OpenAPI Docs, Pagination, Health Probes)"]
        UI["React 18 + Vite Dashboard - Port 5173<br/>(APDI Explorer, Scorecards, Player Profiles)"]
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

    INGEST->>SRC: Discover and Fetch Raw Asset (JSON / HTML)
    SRC-->>INGEST: Raw Response Payload
    INGEST->>SHA: Compute SHA-256 Hash of Raw Content
    SHA->>DB: Check if Content Hash Exists (source_records)
    alt Hash Already Present (Idempotent Skip)
        DB-->>INGEST: Duplicate Detected - Log SKIPPED
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
    RAW["Raw Editorial Text<br/>(HTML / RSS Articles)"] --> CLEAN["Text Cleaner<br/>- HTML Unescape<br/>- Boilerplate Strip<br/>- Unicode Normalization"]
    
    CLEAN --> TOK["Cricket Tokenizer<br/>- Overs (19.4)<br/>- Scores (176/7)<br/>- Acronyms (IND, SA)"]
    
    TOK --> GAZ["Gazetteer Matcher<br/>- Boundary Anchoring<br/>- Longest-Phrase Priority<br/>- Substring Guard"]
    
    GAZ --> ER["Entity Disambiguator<br/>- Context Linker<br/>- Alias Canonicalization<br/>- Ambiguity Flagging"]
    
    ER --> MENT["entity_mentions<br/>(Resolved IDs, Character Spans)"]
    
    MENT --> SENT["Aspect Sentiment Engine<br/>- Negation Windowing<br/>- Batter vs Bowler Context<br/>- Domain Lexicons"]
    
    SENT --> FRAME["sentiment_baselines<br/>(Framing Scores, Publisher Breakdown)"]
```

---

### 1.4 Attention-to-Performance Discrepancy Index (APDI) Architecture

The APDI formula mathematically measures divergence between editorial media attention and objective athletic performance across standardized role cohorts (Batters, Bowlers, Teams).

```mermaid
flowchart TD
    subgraph PerfTrack["Objective Match Performance"]
        DELIV["Ball-by-Ball Deliveries<br/>(2,314 Records)"] --> CALC_P["Compute Raw Performance Composite<br/>- Batting: Runs, Strike Rate, 4s, 6s, Average<br/>- Bowling: Economy, Wickets, Maidens, Strike Rate<br/>- Team: Win %, Run Rate, Margin"]
        CALC_P --> COHORT_P["Partition into Role Cohorts<br/>(Batters / Bowlers / Teams)"]
        COHORT_P --> RANK_P["Compute Percentile Rank<br/>NormPerf = Rank / (N - 1) in [0.0, 1.0]"]
    end

    subgraph AttnTrack["Editorial Media Visibility"]
        TEXT["Editorial Corpus<br/>(Articles and Paragraphs)"] --> CALC_A["Compute Raw Media Attention Composite<br/>- Mention Volume (Paragraphs vs Raw)<br/>- Article Reach and Publisher Diversity<br/>- Position Prominence (Headline=3.0, Lead=1.5, Body=1.0)"]
        CALC_A --> COHORT_A["Partition into Role Cohorts<br/>(Batters / Bowlers / Teams)"]
        COHORT_A --> RANK_A["Compute Percentile Rank<br/>NormAttn = Rank / (N - 1) in [0.0, 1.0]"]
    end

    subgraph QualityGate["Evidence Sufficiency and Eligibility Gate"]
        SAMPLE["Sufficient Sample Size?<br/>- Cohort Size N >= 5<br/>- Batter Balls >= 10<br/>- Bowler Overs >= 2.0<br/>- Team Matches >= 1"]
    end

    RANK_P --> SAMPLE
    RANK_A --> SAMPLE

    SAMPLE -->|No: Below Threshold| INSUF["INSUFFICIENT_DATA<br/>- APDI = NULL (Strict Zero-Fabrication)<br/>- Category = INSUFFICIENT_DATA<br/>- Retain Sample Indicators and Warnings"]
    SAMPLE -->|Yes: Meets Threshold| FORMULA["APDI Formulation<br/>APDI = NormAttn - NormPerf in [-1.0, +1.0]"]

    FORMULA --> CLASSIFY["Discrepancy Category Threshold<br/>(Threshold = 0.20)"]
    CLASSIFY -->|APDI above +0.20| OVER["OVER_ATTENDED<br/>(Attention outstrips performance)"]
    CLASSIFY -->|APDI below -0.20| UNDER["UNDER_ATTENDED<br/>(Performance outstrips attention)"]
    CLASSIFY -->|APDI between -0.20 and +0.20| BAL["BALANCED<br/>(Attention aligns with performance)"]

    INSUF --> PERSIST["Persist to apdi_records Table"]
    OVER --> PERSIST
    UNDER --> PERSIST
    BAL --> PERSIST
```

---

### 1.5 Database Schema & Entity Relationship Model

The underlying SQLite database (`data/cricket_intel.db`, Schema Version 5) strictly enforces foreign-key relationships, transactional guarantees, and WAL mode.

```mermaid
erDiagram
    TEAMS ||--o{ MATCHES : plays
    TEAMS ||--o{ PLAYERS : rosters
    MATCHES ||--o{ DELIVERIES : contains
    PLAYERS ||--o{ DELIVERIES : participates
    SOURCE_RECORDS ||--o{ MATCHES : verifies
    SOURCE_RECORDS ||--o{ ARTICLES : verifies
    ARTICLES ||--o{ ARTICLE_PARAGRAPHS : contains
    ARTICLE_PARAGRAPHS ||--o{ ENTITY_MENTIONS : mentions
    PLAYERS ||--o{ PERFORMANCE_METRICS : evaluates
    PLAYERS ||--o{ ATTENTION_METRICS : measures
    PLAYERS ||--o{ APDI_RECORDS : scores
    ANALYTICS_RUNS ||--o{ APDI_RECORDS : generates

    MATCHES {
        string match_id PK
        string tournament
        string match_date
        string venue
        string team1_id FK
        string team2_id FK
        string winner_id
        string provenance_id FK
    }

    DELIVERIES {
        string delivery_id PK
        string match_id FK
        int innings
        int over_num
        int ball_num
        string batter_id FK
        string bowler_id FK
        int batter_runs
        int extra_runs
        int total_runs
        boolean is_wicket
        string wicket_kind
        string phase
    }

    PLAYERS {
        string player_id PK
        string full_name
        string cricsheet_id
        string primary_team_id FK
        string batting_style
        string bowling_style
        string aliases_json
    }

    TEAMS {
        string team_id PK
        string name
        string code
        string aliases_json
    }

    SOURCE_RECORDS {
        string provenance_id PK
        string source_name
        string source_url
        string content_hash_sha256
        string license_tag
        boolean redistributable
    }

    ARTICLES {
        string article_id PK
        string title
        string url
        string source_domain
        string published_date
        string provenance_id FK
    }

    ARTICLE_PARAGRAPHS {
        string paragraph_id PK
        string article_id FK
        int paragraph_index
        string text
        string section_type
    }

    ENTITY_MENTIONS {
        string mention_id PK
        string paragraph_id FK
        string surface_text
        string entity_type
        string resolved_id
        string resolution_status
    }

    PERFORMANCE_METRICS {
        string metric_id PK
        string entity_id FK
        string role
        string tournament
        int matches_played
        int runs_scored
        float strike_rate
        int wickets_taken
        float bowling_economy
        float raw_performance_composite
    }

    ATTENTION_METRICS {
        string metric_id PK
        string entity_id FK
        string tournament
        int paragraph_count
        int raw_mention_count
        int article_reach
        int source_diversity_count
        float prominence_score
        float raw_attention_composite
    }

    APDI_RECORDS {
        string record_id PK
        string run_id FK
        string entity_id FK
        string entity_name
        string role_cohort
        float raw_attention_score
        float normalized_attention_score
        float raw_performance_score
        float normalized_performance_score
        float apdi_value
        string discrepancy_category
        string evidence_sufficiency_status
    }

    ANALYTICS_RUNS {
        string run_id PK
        string tournament
        string status
        int entities_processed
        int valid_apdi_count
        int insufficient_data_count
        string completed_at_utc
    }
```

---

### 1.6 Full-Stack Application Component Hierarchy

The platform provides a dual-surface architecture: a high-throughput FastAPI REST API serving typed JSON contracts, and a responsive React 18 / Vite single-page dashboard.

```mermaid
flowchart TB
    subgraph Browser["User Browser - Port 5173"]
        SHELL["App Shell and Navigation Sidebar<br/>(Header, Theme Toggle, Active Tournament Scope)"]
        
        subgraph Views["Dashboard Application Views"]
            V1["Overview Dashboard<br/>(KPI Cards, Pipeline Status, Attention BarCharts, Health)"]
            V2["Matches Explorer and Scorecard<br/>(Fixture List, Innings Aggregates, Batting and Bowling Scorecards)"]
            V3["Player Directory and Research Profile<br/>(Interactive Table, Full Names, Bat/Bowl Styles, Rich Profile)"]
            V4["APDI Discrepancy Explorer<br/>(Mathematical Matrix, Cohort Filters, Discrepancy Badges)"]
            V5["Media Intelligence and Articles<br/>(Editorial Harvest Corpus, Paragraph Splitter, Entity Offsets)"]
            V6["Topics and Narratives<br/>(KMeans Cluster Clouds, Dominant Themes, Keyword Distributions)"]
            V7["System Health and Observability<br/>(4-Tier Audit: Liveness, Storage, Corpus, APDI Invariants)"]
            V8["Provenance and Data Sources<br/>(Immutable SHA-256 Catalog, Ingestion Audit Runs, Licensure)"]
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

    subgraph ClientLib["Frontend API Client"]
        RQ["TanStack React Query<br/>(Caching, Invalidation, Error Boundaries)"]
        AXIOS["Axios HTTP Client<br/>(Base URL: http://127.0.0.1:8000)"]
        RQ --> AXIOS
    end

    Views --> RQ

    subgraph BackendAPI["FastAPI REST Application - Port 8000"]
        CORS["CORS Middleware<br/>(Strict Origin Whitelist)"]
        LIFE["Lifespan Context Manager<br/>(SQLite Persistence Binding)"]
        ERR["Standardized Error Handlers<br/>(400, 404, 422, 500 JSON Envelopes)"]
        
        subgraph Routers["API v1 Route Controllers"]
            R_HEALTH["Health and Readiness Endpoints"]
            R_MATCH["Matches and Performance Endpoints"]
            R_PLAY["Players and Teams Endpoints"]
            R_ART["Articles and Paragraphs Endpoints"]
            R_NLP["Topics and Entities Endpoints"]
            R_ANLY["Analytics and APDI Endpoints"]
            R_OBS["Observability and Sources Endpoints"]
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
    START(["Run: python -m src.pipeline.cli run"]) --> STEP1["1. Ingestion and Adapters<br/>- Ingest Cricsheet Matches and Deliveries<br/>- Ingest Editorial Tournament Articles"]
    STEP1 --> STEP2["2. Text Processing and NLP<br/>- Extract Paragraphs and Strip Boilerplate<br/>- Cricket Tokenization and Entity Extraction<br/>- Aspect-Based Sentiment Framing"]
    STEP2 --> STEP3["3. Topic Clustering<br/>- Dense Sentence Embeddings<br/>- KMeans Topic Clustering k=3"]
    STEP3 --> STEP4["4. Objective Performance<br/>- Aggregate Deliveries by Batter, Bowler, Team<br/>- Compute Raw Performance Composites"]
    STEP4 --> STEP5["5. Media Attention Calculation<br/>- Aggregate Mentions, Reach, Prominence<br/>- Compute Raw Attention Composites"]
    STEP5 --> STEP6["6. APDI Calculation Engine<br/>- Resolve Cross-Entity Aliases<br/>- Evaluate Minimum Sample Gates<br/>- Compute APDI and Classify Discrepancy"]
    STEP6 --> STEP7["7. Player Metadata Enrichment<br/>- Align Full Names, Batting and Bowling Styles"]
    STEP7 --> STEP8["8. Analytical Summary Report<br/>- Display Final Terminal Metrics and Invariant Checks"]
    STEP8 --> END(["Pipeline Completed Successfully"])
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
