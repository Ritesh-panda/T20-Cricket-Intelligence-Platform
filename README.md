# T20 Cricket Intelligence Platform
### Open-Source Sports Intelligence, Narrative Discovery & Event Grounding for T20 Cricket

An end-to-end sports intelligence and NLP research system that bridges the gap between **unstructured cricket media (news articles, expert analysis, editorial tournament reports)** and **structured match facts (ball-by-ball deliveries, wickets, and phases from Cricsheet)**.

The platform introduces the **Attention-to-Performance Discrepancy Index (APDI)**, quantifying the mathematical divergence between media attention prominence and objective athletic output across role cohorts (Batters, Bowlers, Teams).

---

## 📚 Essential Guides & Documentation

- 📖 **[USER_GUIDE.md](docs/USER_GUIDE.md)**: **Complete User Manual** covering setup, React dashboard walkthrough (APDI Explorer, Match Explorer, Player Profiles, Media Intelligence, Topics, Sources), API reference, and APDI interpretation.
- 🧪 **[TESTING_AND_QA_GUIDE.md](docs/TESTING_AND_QA_GUIDE.md)**: **Complete Tester's Specification & Function Guide** detailing test execution, function-by-function testing reference, invariants, edge cases, and QA acceptance checklists.
- 📋 **[PHASE_9_RELEASE_CHECKLIST.md](docs/PHASE_9_RELEASE_CHECKLIST.md)**: Item-by-item release verification and research integrity sign-offs.
- ⚖️ **[PHASE_9_SOURCE_LEGALITY_AUDIT.md](docs/PHASE_9_SOURCE_LEGALITY_AUDIT.md)**: Exhaustive compliance audit of all data sources across 11 legal dimensions.
- 📐 **[PHASE_9_APDI_METHODOLOGY.md](docs/PHASE_9_APDI_METHODOLOGY.md)**: In-depth mathematical review and numerical sensitivity analysis of the APDI formula.

---

## ⚡ Quickstart: Running Locally

### 1. Prerequisites
- Python 3.11+ (verified on 3.13)
- Node.js 18+ and npm
- SQLite 3 (WAL mode supported)

### 2. Backend Setup & Launch
```bash
# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install Python requirements
pip install -r requirements.txt

# Start FastAPI backend (runs on http://127.0.0.1:8000)
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```
*OpenAPI Documentation*: Navigate to `http://127.0.0.1:8000/docs` in your browser.

### 3. Frontend Setup & Launch
```bash
cd frontend
npm install

# Start Vite development server (runs on http://127.0.0.1:5173)
npm run dev
```
*Web Application*: Navigate to `http://127.0.0.1:5173/` in your browser.

---

## 🧪 Testing & Quality Assurance

```bash
# Run full Python regression test suite (112 tests)
python -m pytest tests/ -v

# Run frontend test suite (9 tests)
cd frontend
npm run test

# Run frontend TypeScript type checking
npm run typecheck

# Build frontend production bundle
npm run build

# Run ground-truth scorecard validation script (10/10 matches, 2314 deliveries)
python scripts/validate_raw_matches_against_db.py

# Run APDI sensitivity analysis script
python scripts/phase9_apdi_sensitivity.py

# Run NLP gold-set evaluation benchmark (N=20)
python scripts/evaluate_nlp_gold_set.py
```

---

## 🏛️ System Architecture

```
[01. Data Acquisition & Adapters]
  └── Cricsheet Open Data (ODC-By 1.0) + Wikimedia Editorial Reports (CC BY-SA 4.0)
        │
[02. Extraction, Normalization & Validation]
  └── Trafilatura text extraction + Pydantic v2 validation + SHA-256 deduplication
        │
[03. Persistence Layer]
  └── SQLite (data/cricket_intel.db, Schema Version 5 with WAL mode)
        │
[04. Cricket NLP & Match Analytics]
  └── Cricket NER & gazetteer entity resolution + Aspect sentiment + Sentence Transformers
        │
[05. Reasoning, Clustering & Discrepancy Analytics]
  └── KMeans topic clusters (k=3) + APDI calculation engine (Normalized Attention - Normalized Performance)
        │
[06. Serving & Presentation]
  └── FastAPI REST backend (:8000) + React/Vite sports intelligence dashboard (:5173)
```

---

## 📊 Key Verified Metrics (ICC Men's T20 World Cup 2024)

- **Matches Verified**: 10 matches (100% exact parity with raw Cricsheet JSON).
- **Deliveries Verified**: 2,314 ball-by-ball records.
- **Editorial Text**: 5 Wikimedia articles, 314 paragraphs, 683 entity mentions.
- **Topic Clusters**: 3 distinct clusters (Historical Rivalry, Match Action, Squad Rosters).
- **Entities Evaluated**: 116 unique entities (107 players + 9 teams).
- **APDI Evaluation**: 13 Valid entities (7 Balanced, 3 Over-Attended, 3 Under-Attended) and 103 low-sample entities strictly preserved with `NULL` scores (`INSUFFICIENT_DATA`).
- **Test Suite**: 112 passing Python tests, 9 passing frontend tests, 0 TypeScript errors.

---

## 📜 License & Compliance Notice

- **Structured Cricket Data**: Provided by [Cricsheet](https://cricsheet.org/) under the [Open Data Commons Attribution License (ODC-By 1.0)](https://opendatacommons.org/licenses/by/1-0/).
- **Editorial Summaries**: Sourced from [Wikipedia / Wikimedia Foundation](https://en.wikipedia.org/) under [Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).
- **Ethical Web Scraping Protocol**: The platform adheres strictly to `robots.txt` directives. Commercial publishers with restrictive terms (ESPNcricinfo, Cricbuzz, Wisden) are categorized as `RESTRICTED` and withheld from automated scraping.
