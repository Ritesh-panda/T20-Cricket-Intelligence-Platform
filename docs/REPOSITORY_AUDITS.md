# Repository Audits: Candidate Open-Source Projects

This document contains formal 5-pillar audit cards for all nine candidate open-source cricket intelligence repositories evaluated for the T20 Cricket Intelligence Platform.

---

## 1. Audit Summary Matrix

| Repo # | Candidate Name | Upstream URL | Commit Hash | License | Score (25) | Decision | Primary Role / Disposition |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **01** | **ZainZoy/NLP-project** | `https://github.com/ZainZoy/NLP-project` | `76578b46787acf6408d64b0d49c233e27de029c0` | Missing (None) | 18/25 | **ADAPT** | Adapt commentary regex grammar, scoring rules, and validation checks into canonical Pydantic architecture. |
| **02** | **princyhareshbhai1530/T20-Commentary-Analysis** | `https://github.com/princyhareshbhai1530/T20-Commentary-Analysis` | `af64837c57b3163c2e181e76cf4b82683f17cc83` | Mentioned MIT in README, no file | 9/25 | **REFERENCE ONLY** | Reference excitement keywords and phase concepts; reject monolithic script and flawed ML split. |
| **03** | **HalcyonVector/Cricket-Intelligence-Lab** | `https://github.com/HalcyonVector/Cricket-Intelligence-Lab` | `57be3daf1f92bdcca55eb8ce95fbcd1c1a3409f9` | None (ODbL / CC BY-SA for data) | 19/25 | **ADAPT** | Adapt lightweight Cricbuzz Next.js JSON extraction heuristic and Cricsheet `orjson` parser into polite adapters. |
| **04** | **vinaybale-collab/cricket-analytics-web** | `https://github.com/vinaybale-collab/cricket-analytics-web` | `4cffafabdf0eef30db05cc6c41134221f26f2d97` | None (CC BY 4.0 for data) | 12/25 | **REFERENCE ONLY** | Reference DuckDB SQL queries and Next.js dashboard layout; reject monolithic code and cloud API lock-in. |
| **05** | **Anurag9557/cricket-iq** | `https://github.com/Anurag9557/cricket-iq` | `8c67a120b85ada7855bfaeaa161951277ded1781` | **MIT License** | **23/25** | **REUSE / ADAPT** | Reuse Polars-based chase state builder, verification gates, and Parquet pipeline directly with MIT attribution. |
| **06** | **ShrinathSontakke/Cricket-Data-Analytics** | `https://github.com/ShrinathSontakke/Cricket-Data-Analytics` | `1448b257bc935541b8d48edfdcb5b17ea7171d02` | None | 6/25 | **REJECT** | Reject proprietary PowerBI `.pbix` binaries and paid Web Unlocker scraping scripts. |
| **07** | **Paul-ans-typ/Analysis-of-Cricket-Commentary** | `https://github.com/Paul-ans-typ/Analysis-of-Cricket-Commentary` | `e580d8faa0d37b463ab26677d22aded5e4099d77` | None | 6/25 | **REJECT** | Reject dangerous RNN score predictor from commentary and unverified binary pickle execution. |
| **08** | **sst-cloud-solutions/h25-sports** | `https://github.com/sst-cloud-solutions/h25-sports` | `47bbce76226603aa1b6a6b4bf9fa21241338d6a3` | **UNLICENSED (Private)** | 7/25 | **REJECT** | Hard license blocker (explicitly UNLICENSED private hackathon code); mock biometrics unsuited for T20 project. |
| **09** | **SRIHARI18V/CRICKET-RAG-CHATBOT** | `https://github.com/SRIHARI18V/CRICKET-RAG-CHATBOT` | `f94d1b9668c8ca47ecb484c7ad5d03635b74f1ae` | None | 13/25 | **REFERENCE ONLY** | Reference structured vs unstructured query router concept; reject unlicenced code and cloud Anthropic dependency. |

---

## 2. Detailed Audit Cards

### [Audit-01] ZainZoy/NLP-project
- **Upstream URL**: `https://github.com/ZainZoy/NLP-project`
- **Evaluated Commit**: `76578b46787acf6408d64b0d49c233e27de029c0`
- **License**: Missing (No license file or declaration; default all rights reserved).
- **Primary Domain**: Deterministic Commentary Parsing, Score Verification, Turning Point Detection.

#### Technical Analysis
- **Core Capabilities**: Highly disciplined rule-based commentary parser enforcing the core principle "Accuracy First". Never invents numbers; includes validation gates cross-checking runs + extras vs team total and dismissals vs wickets. Includes turning-point detection with commentary evidence strings and impact player scoring.
- **Dependencies**: Pandas, NumPy, Plotly, Streamlit. Optional: spaCy, NLTK, Transformers (falls back cleanly to rule-based if absent).
- **Limitations / Technical Debt**: No software license file. Streamlit UI is tightly coupled to module execution. Ingestion is manual file upload rather than an automated pipeline.
- **Security Assessment**: Safe; no suspicious network requests or dangerous runtime deserialization.
- **Rubric Scoring**:
  - Licensing: 2/5 (Missing license prevents direct file copying)
  - Security: 5/5
  - Architecture: 4/5 (Clean module separation: parser, analytics, validation, summarization)
  - Code Quality: 4/5 (Docstrings, type hints, dataclasses, pytest suite)
  - Maintenance: 3/5
  - **Total**: **18/25**
- **Decision**: **ADAPT**. We will adapt the commentary grammar, scoring rules, and validation gate logic into our canonical Pydantic architecture (`src/adapters/commentary_parser.py` and `src/models/validation_gate.py`).

---

### [Audit-02] princyhareshbhai1530/T20-Commentary-Analysis
- **Upstream URL**: `https://github.com/princyhareshbhai1530/T20-Commentary-Analysis`
- **Evaluated Commit**: `af64837c57b3163c2e181e76cf4b82683f17cc83`
- **License**: Mentions "MIT License" in README text, but no LICENSE file in repo.
- **Primary Domain**: Single-script Commentary ML & Matplotlib Visualizations.

#### Technical Analysis
- **Core Capabilities**: Computes basic phase bands, excitement scores via keyword matching, and trains a RandomForestClassifier for win probability on a static CSV.
- **Dependencies**: Pandas, NumPy, Matplotlib, Seaborn, TextBlob, Scikit-Learn.
- **Limitations / Technical Debt**: Monolithic 176-line Colab-style script. Data leakage in ML split (`train_test_split` on random rows within the same match). Naive TextBlob sentiment unsuited for cricket context. No tests, no API, no package structure.
- **Security Assessment**: Safe.
- **Rubric Scoring**:
  - Licensing: 3/5
  - Security: 4/5
  - Architecture: 1/5 (Monolithic script)
  - Code Quality: 2/5
  - Maintenance: 2/5 (Static repository)
  - **Total**: **9/25**
- **Decision**: **REFERENCE ONLY**. Keep the domain excitement keyword list (`["six", "smash", "crush", "out", "bowled", "catch", "huge", "massive"]`) in our gazetteer. Reject code implementation.

---

### [Audit-03] HalcyonVector/Cricket-Intelligence-Lab
- **Upstream URL**: `https://github.com/HalcyonVector/Cricket-Intelligence-Lab`
- **Evaluated Commit**: `57be3daf1f92bdcca55eb8ce95fbcd1c1a3409f9`
- **License**: None for software code (README references Cricsheet ODbL/CC BY-SA data license).
- **Primary Domain**: Cricbuzz Streaming Scraper & Cricsheet Ingestion.

#### Technical Analysis
- **Core Capabilities**: Discovers that Cricbuzz inlines its structured match data inside Next.js streaming payloads (`self.__next_f.push([...])`), enabling fast HTTP extraction of live scores, schedules, commentary, and player profiles without headless browsers or Akamai blocks. High-performance Cricsheet JSON parser using `orjson` resolving stable 8-hex player IDs via `info.registry.people`.
- **Dependencies**: Python stdlib, `requests`, `orjson`, `numpy`.
- **Limitations / Technical Debt**: No root LICENSE file. In-memory caching and custom stdlib HTTP server instead of FastAPI.
- **Security Assessment**: Safe. Uses legitimate public page fetches with user-agent headers.
- **Rubric Scoring**:
  - Licensing: 2/5
  - Security: 5/5
  - Architecture: 4/5 (Clean ETL packages: `cil_etl/parse.py`, `ingest_zip.py`)
  - Code Quality: 4/5 (High performance, type hints)
  - Maintenance: 4/5 (Active, comprehensive coverage across 48 cohorts)
  - **Total**: **19/25**
- **Decision**: **ADAPT**. Adapt the Cricbuzz Next.js JSON extraction heuristic and Cricsheet `orjson` parser into `src/adapters/cricbuzz_adapter.py` and `src/adapters/cricsheet_adapter.py` under our canonical Pydantic validation.

---

### [Audit-04] vinaybale-collab/cricket-analytics-web
- **Upstream URL**: `https://github.com/vinaybale-collab/cricket-analytics-web`
- **Evaluated Commit**: `4cffafabdf0eef30db05cc6c41134221f26f2d97`
- **License**: None for web app code (references Cricsheet CC BY 4.0).
- **Primary Domain**: FastAPI + DuckDB Analytics + Next.js UI.

#### Technical Analysis
- **Core Capabilities**: Analytical DuckDB SQL queries over Cricsheet data; free-tier rate limiter protecting Google Gemini API calls; Next.js 15 + Tailwind CSS interactive dashboard.
- **Dependencies**: FastAPI, DuckDB, `google-genai`, Next.js, React, Tailwind CSS.
- **Limitations / Technical Debt**: Monolithic 1,614-line `main.py` backend mixing SQL queries, rate limits, prompts, and route handlers. Hard dependency on cloud Gemini API keys. Zero test suite.
- **Security Assessment**: Safe, but exposes Gemini rate limiting logic.
- **Rubric Scoring**:
  - Licensing: 2/5
  - Security: 4/5
  - Architecture: 2/5 (1600-line monolithic file)
  - Code Quality: 3/5
  - Maintenance: 3/5
  - **Total**: **12/25**
- **Decision**: **REFERENCE ONLY**. Reference the analytical DuckDB queries and frontend UI components. Reject copying backend code due to monolithic design and cloud API lock-in.

---

### [Audit-05] Anurag9557/cricket-iq
- **Upstream URL**: `https://github.com/Anurag9557/cricket-iq`
- **Evaluated Commit**: `8c67a120b85ada7855bfaeaa161951277ded1781`
- **License**: **MIT License** (Verified in root `LICENSE` file).
- **Primary Domain**: Polars Ball-by-Ball Chase State Builder, Win Probability, Verification Gate.

#### Technical Analysis
- **Core Capabilities**: Exemplary sports analytics engineering. Uses `polars` for lightning-fast vectorized cumulative chase state generation (runs needed, balls remaining, required run rate, momentum windows). Shipped calibrated LightGBM win-probability model (Brier 0.114, AUC 0.92). Deterministic verification gate preventing generative LLMs from stating unverified statistics. Server-Sent Events (SSE) live replay engine.
- **Dependencies**: Polars, LightGBM, FastAPI, Pydantic, Scikit-Learn, Pytest.
- **Limitations / Technical Debt**: Focused primarily on second-innings chase states rather than media journalism.
- **Security Assessment**: Exemplary. Zero dangerous dependencies, zero credential leaks.
- **Rubric Scoring**:
  - Licensing: 5/5 (Permissive MIT license)
  - Security: 5/5
  - Architecture: 5/5 (Clean modular package `cricketiq/{core, data, models, explain, api}`)
  - Code Quality: 5/5 (Type hints, docstrings, comprehensive Pytest suite)
  - Maintenance: 4/5
  - **Total**: **23/25**
- **Decision**: **REUSE / ADAPT**. Directly integrate the Polars chase-state builder (`src/cricketiq/data/state_builder.py`) and verification gate patterns into our `src/analytics/` module with proper MIT attribution in `LICENSES.md`.

---

### [Audit-06] ShrinathSontakke/Cricket-Data-Analytics
- **Upstream URL**: `https://github.com/ShrinathSontakke/Cricket-Data-Analytics`
- **Evaluated Commit**: `1448b257bc935541b8d48edfdcb5b17ea7171d02`
- **License**: None.
- **Primary Domain**: PowerBI `.pbix` Reports & Web Unlocker Scraper Scripts.

#### Technical Analysis
- **Core Capabilities**: PowerBI dashboard mockups and JavaScript scraper scripts designed for Bright Data Web Unlocker to scrape ESPNcricinfo.
- **Dependencies**: PowerBI Desktop, Bright Data paid proxy service.
- **Limitations / Technical Debt**: Proprietary binary PowerBI files cannot be run or automated in CI/Python. Scrapers rely on paid residential proxy services. No Python codebase, no tests, no license.
- **Security Assessment**: Third-party proxy credentials required.
- **Rubric Scoring**:
  - Licensing: 1/5
  - Security: 3/5
  - Architecture: 1/5
  - Code Quality: 1/5
  - Maintenance: 2/5
  - **Total**: **6/25**
- **Decision**: **REJECT**. Incompatible with open-source, automated local-first architecture.

---

### [Audit-07] Paul-ans-typ/Analysis-of-Cricket-Commentary
- **Upstream URL**: `https://github.com/Paul-ans-typ/Analysis-of-Cricket-Commentary`
- **Evaluated Commit**: `e580d8faa0d37b463ab26677d22aded5e4099d77`
- **License**: None.
- **Primary Domain**: RNN-based Score Prediction from Commentary Text.

#### Technical Analysis
- **Core Capabilities**: Attempts to use an RNN to predict runs and wickets from commentary text sequences.
- **Dependencies**: TensorFlow, Keras, NLTK, Pandas, Pickle.
- **Limitations / Technical Debt**: Anti-pattern design: predicting numeric scores using machine learning when exact scores are already available in Cricsheet and structured scorecards. Loads unverified binary `trained_model.pkl`. 5,700 uncompressed CSV files committed to repo. No tests, no license.
- **Security Assessment**: Low (arbitrary `pickle.load` of unverified models).
- **Rubric Scoring**:
  - Licensing: 1/5
  - Security: 2/5
  - Architecture: 1/5
  - Code Quality: 1/5
  - Maintenance: 1/5
  - **Total**: **6/25**
- **Decision**: **REJECT**. Inaccurate architecture, dangerous pickle deserialization, and redundant capability.

---

### [Audit-08] sst-cloud-solutions/h25-sports
- **Upstream URL**: `https://github.com/sst-cloud-solutions/h25-sports`
- **Evaluated Commit**: `47bbce76226603aa1b6a6b4bf9fa21241338d6a3`
- **License**: **UNLICENSED (Explicit Private Project Notice in README)**.
- **Primary Domain**: NestJS Microservices + Next.js Platform with Twitter Sentiment.

#### Technical Analysis
- **Core Capabilities**: NestJS microservices backend, Next.js frontend, Twitter API integration for fan sentiment, and mock feeds for player biometrics/physics.
- **Dependencies**: Node.js, NestJS, Next.js, Google Gemini, Twitter API.
- **Limitations / Technical Debt**: Explicit license blocker (`UNLICENSED - Private project for hackathon submission`). Relying on mock data and paid Twitter/Gemini APIs.
- **Security Assessment**: Requires Twitter and Google API keys.
- **Rubric Scoring**:
  - Licensing: 0/5 (Hard legal blocker)
  - Security: 3/5
  - Architecture: 3/5
  - Code Quality: 3/5
  - Maintenance: 2/5
  - **Total**: **7/25**
- **Decision**: **REJECT (LICENSE BLOCKER)**. Cannot copy or reuse any code or assets under copyright law.

---

### [Audit-09] SRIHARI18V/CRICKET-RAG-CHATBOT
- **Upstream URL**: `https://github.com/SRIHARI18V/CRICKET-RAG-CHATBOT`
- **Evaluated Commit**: `f94d1b9668c8ca47ecb484c7ad5d03635b74f1ae`
- **License**: None.
- **Primary Domain**: Hybrid Query Router (Structured Stats vs Unstructured RAG).

#### Technical Analysis
- **Core Capabilities**: Introduces a query router that classifies user questions into structured stats queries (evaluated over Cricsheet Pandas/SQL) versus unstructured narrative queries (evaluated over vector embeddings of match reports in Chroma).
- **Dependencies**: Anthropic API, Chroma, Pandas, Streamlit.
- **Limitations / Technical Debt**: No license file. Nested directory structure (`cricket-rag/cricket-rag`). Hard dependency on Anthropic Claude API keys and cloud Chroma vector DB.
- **Security Assessment**: Safe, but requires proprietary API keys.
- **Rubric Scoring**:
  - Licensing: 2/5
  - Security: 4/5
  - Architecture: 4/5 (Clean conceptual router separation)
  - Code Quality: 3/5
  - Maintenance: 2/5
  - **Total**: **13/25**
- **Decision**: **REFERENCE ONLY / ADAPT CONCEPT**. The query routing concept (separating structured match statistics queries from unstructured narrative/commentary retrieval) is valuable and will inform our API and explainability service, but we will not copy the unlicenced code.
