# Phase 8 — Platform Release & Deployment Readiness Checklist

**Project:** T20 Cricket Intelligence Platform  
**Target Release:** Research Release v1.0.0  
**Audit Date:** 2026-10-24  
**Audit Standard:** Strict Research Integrity & Reproducibility  

---

## 1. Security, Secrets, and Privacy Gate

- [x] **No Secrets or Tokens Tracked:**
  - Audited `git status` and Git tree for `api_key`, `secret`, `private_key`, `password`, or auth tokens: **0 findings**.
- [x] **Database Files Excluded from Git:**
  - `data/*.db`, `*.db-shm`, `*.db-wal`, `*.db.bak*` properly ignored via `.gitignore`.
  - Confirmed via `git ls-files data/`: only `data/evaluation/nlp_gold_set.json` is tracked.
- [x] **Raw Restricted Data Excluded:**
  - `data/raw/` and `data/cache/` ignored by Git.
  - Raw HTML and JSON files are not exposed in the Git history.
- [x] **Local Development Binding:**
  - FastAPI configured for local development (`127.0.0.1:8000`).
  - CORS strictly configured to localhost/127.0.0.1 origins without wildcard credentials.
- [x] **Public Exception Sanitization:**
  - Internal database stack traces are caught by custom exception handlers; 404, 422, and 500 responses return clean JSON schemas without revealing internal server paths.

---

## 2. Licensing and Provenance Gate

- [x] **Tier A (Cricsheet Structured Matches):**
  - Ingested under Open Database License (ODbL 1.0) / Open Data Commons Attribution License (ODC-By 1.0).
  - Explicit attribution "Data provided by Cricsheet.org" recorded in database provenance records and UI footers.
- [x] **Tier B (Wikimedia Foundation Editorial Prose):**
  - Ingested under Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA 4.0).
  - Full canonical URLs, page titles, and MediaWiki revision IDs tracked in `editorial_manifest.json` and `source_records`.
- [x] **Tier C (Commercial Commentary):**
  - Restricted by commercial copyright and `robots.txt` disallows (ESPNcricinfo, Cricbuzz, Wisden).
  - Explicitly documented as uncollected; no unauthorized scraping and zero synthetic commentary records fabricated.

---

## 3. Data Integrity & Domain Invariant Gate

- [x] **Ball-by-Ball Scorecard Ground-Truth Invariants:**
  - Verified across all 10 matches (2,314 deliveries).
  - Innings runs, batter runs, extras, wickets, legal balls, wides, and no-balls match source JSON to 100% exact parity.
- [x] **Match & Delivery Referential Integrity:**
  - 0 orphaned deliveries; all delivery records reference valid match IDs.
- [x] **Super Over & DLS Handling:**
  - Match 1415711 (Pakistan vs USA Super Over) correctly partitioned across innings 1–4.
  - Match 1415744 (Bangladesh vs Australia) and Match 1415750 (West Indies vs South Africa) DLS targets and revised scores preserved accurately.
- [x] **Document Scope Integrity:**
  - Only genuine single-match articles carry `linked_match_id` (Match 1415755 Final). Broad tournament overviews, rosters, and historical pages have `linked_match_id: null`.

---

## 4. Analytical Safeguards & Mathematical Gate

- [x] **Percentile Ranking & APDI Formula:**
  - $\text{APDI} = \text{NormAttention} - \text{NormPerformance}$ independently verified via hand-calculated scripts.
- [x] **Strict Minimum Sample Size Safeguards:**
  - Entities with sub-threshold evidence or 0 media mentions receive `evidence_sufficiency_status = 'INSUFFICIENT_DATA'` and `apdi_value = NULL`.
  - Zero fabricated APDI scores across the 103 low-sample entities.
- [x] **Normalization Bounds:**
  - Normalized attention and performance scores strictly bounded within $[0.0, 1.0]$.
  - Zero out-of-bounds metrics verified via `/api/v1/analytics/validation`.

---

## 5. Software Engineering & Build Gate

- [x] **Python Regression Test Suite:**
  - Command: `pytest tests/`
  - Result: **104 passed** in 19.23s (0 failures, 0 errors).
- [x] **Frontend Vitest Test Suite:**
  - Command: `npm run test` (in `frontend/`)
  - Result: **9 passed** across 3 test files (0 failures).
- [x] **Frontend TypeScript Compilation:**
  - Command: `npm run typecheck` (in `frontend/`)
  - Result: **0 errors**.
- [x] **Frontend Production Build:**
  - Command: `npm run build` (in `frontend/`)
  - Result: **Successfully built in 20.47s** (`dist/` generated cleanly).

---

## 6. End-to-End Runtime & Integration Gate

- [x] **Backend REST API:**
  - Running on `http://127.0.0.1:8000`.
  - Swagger UI accessible at `/docs`, ReDoc at `/redoc`, OpenAPI JSON at `/openapi.json`.
  - Endpoint latency across all analytical routes verified between 1.15ms and 25.29ms.
- [x] **React Dashboard:**
  - Running on `http://127.0.0.1:5173`.
  - Overview cards reflect verified corpus: 10 Matches, 2,314 Deliveries, 5 Articles, 116 APDI Records.
  - Matches Directory, APDI Explorer, Topic Clusters, and Diagnostics views render live API data.

---

## 7. Research Release Limitations & Ethical Boundary Declaration

1. **Corpus Scope:** The dataset is bounded to a 10-match sample of the ICC Men's T20 World Cup 2024 and 5 Wikimedia documents. It must **not** be generalized as representative of all global T20 cricket or commercial sports journalism.
2. **APDI Interpretability:** APDI is a descriptive exploratory research metric measuring discrepancies between media attention volume and objective cricket outputs. It does **not** prove journalistic bias, editorial intent, or causality.
3. **No Commercial Scraping:** The absence of Tier C commentary reflects ethical adherence to publisher terms and copyright boundaries.
