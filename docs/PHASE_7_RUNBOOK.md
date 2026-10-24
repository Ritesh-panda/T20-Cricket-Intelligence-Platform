# Phase 7 Operations Runbook: Corpus Ingestion & End-to-End Execution

This runbook provides complete, step-by-step instructions for reproducing the Phase 7 validated corpus, executing analytical pipelines in dependency order, running audits, and starting the API and frontend dashboard.

---

## 1. Prerequisites & Environment Setup

### 1.1 Python Virtual Environment
Ensure Python 3.11+ (Python 3.13 supported) is installed:
```powershell
python --version
pip install -r requirements.txt
```

### 1.2 Frontend Environment
Ensure Node.js 18+ and npm are installed:
```powershell
cd frontend
npm install
cd ..
```

---

## 2. Corpus Acquisition & Verification

Raw source artifacts are stored in `data/raw/` and excluded from git tracking via `.gitignore`.

1. **Verify Raw Cricsheet Matches (Tier A)**:
   ```powershell
   Get-ChildItem data/raw/cricsheet/*.json | Measure-Object
   # Expect 10 match JSON files + corpus_manifest.json
   ```
2. **Verify Editorial Articles (Tier B)**:
   ```powershell
   Get-ChildItem data/raw/editorial/*.html | Measure-Object
   # Expect 5 HTML files + editorial_manifest.json
   ```

---

## 3. Step-by-Step Reproduction Workflow

Execute all pipeline stages in strict dependency order:

### Step 3.1: Ingest Corpus into Primary Database
Ingests 10 Cricsheet matches (2,314 deliveries) and 5 CC-BY-SA editorial articles (314 paragraphs) into `data/cricket_intel.db`:
```powershell
python scripts/ingest_phase7_corpus.py
```
*To verify idempotency, execute the command a second time and verify 0 duplicate rows are created.*

### Step 3.2: Validate Structural & Relational Integrity
Verifies foreign keys, non-negative runs, and paragraph linkage:
```powershell
python -m src.pipeline validate
```

### Step 3.3: Execute Cricket NLP & Entity Resolution
Extracts entity mentions, resolves canonical player/team IDs, and creates sentiment baselines:
```powershell
python -m src.pipeline process-text --all
python -m src.pipeline nlp-stats
python -m src.pipeline nlp-validate
```

### Step 3.4: Evaluate NLP on Curated Gold Set
Runs precision, recall, and resolution benchmark on `data/evaluation/nlp_gold_set.json`:
```powershell
python scripts/evaluate_nlp_gold_set.py
```

### Step 3.5: Compute Semantic Dense Embeddings
Generates 384-dimensional dense vectors using `sentence-transformers/all-MiniLM-L6-v2`:
```powershell
python -m src.pipeline embed-text --model sentence-transformers/all-MiniLM-L6-v2
```

### Step 3.6: Discover Semantic Topics (K-Means Clustering)
Clusters editorial paragraphs and extracts keywords:
```powershell
python -m src.pipeline cluster-topics --k 3
python -m src.pipeline evaluate-topics
```

### Step 3.7: Build Narrative Evolution Timeline
Aggregates narrative sentiment and topic distribution over time:
```powershell
python -m src.pipeline narrative-timeline
python -m src.pipeline analysis-stats
python -m src.pipeline analysis-validate
```

### Step 3.8: Execute Analytics Preflight Quality Gate
Enforces quality gates before calculating metrics:
```powershell
python -m src.pipeline analytics-preflight --tournament "ICC Men's T20 World Cup"
```

### Step 3.9: Compute Media Attention & Performance Metrics
Aggregates paragraph mentions, reach, and on-field ball-by-ball performance:
```powershell
python -m src.pipeline compute-attention --tournament "ICC Men's T20 World Cup"
python -m src.pipeline compute-performance --tournament "ICC Men's T20 World Cup"
```

### Step 3.10: Compute APDI Metrics
Computes Attention-to-Performance Discrepancy Index across cohorts:
```powershell
python -m src.pipeline compute-apdi --tournament "ICC Men's T20 World Cup"
python -m src.pipeline analytics-validate
```

### Step 3.11: Run Independent Analytical Audit
Performs deterministic hand-checks on scorecards, individual metrics, and formulas:
```powershell
python scripts/audit_apdi_calculation.py
```

---

## 4. Starting the Live Application

### 4.1 Start FastAPI Backend Server
```powershell
uvicorn src.api.main:app --port 8000
```
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`
- Matches API: `http://127.0.0.1:8000/api/v1/matches`
- APDI API: `http://127.0.0.1:8000/api/v1/analytics/apdi`

### 4.2 Start React/Vite Research Dashboard
In a separate terminal window:
```powershell
cd frontend
npm run dev
```
- Dashboard Interface: `http://127.0.0.1:5173/`

---

## 5. Automated Regression Test Verification

Run all test suites before committing changes:

```powershell
# Python unit and integration tests (100 tests)
pytest tests/

# Frontend Vitest test suite (9 tests)
cd frontend
npm run test

# Frontend TypeScript type check
npm run typecheck
cd ..
```
