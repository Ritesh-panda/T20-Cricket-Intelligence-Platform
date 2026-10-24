# Phase 7 — Real-World Data Ingestion, End-to-End Validation, and Research Quality Report

## 1. Executive Summary

Phase 7 resolves the evidence gap identified in earlier development phases by acquiring, normalizing, persisting, and evaluating a bounded, legally verified real-world T20 cricket corpus.

Rather than synthesizing mock records or scraping restricted commercial platforms, Phase 7 established an auditable end-to-end pipeline using:
- **Tier A (Structured Ground-Truth Match Deliveries)**: 10 completed matches (2,314 legal and extra deliveries, 107 players, 9 international teams) from the **ICC Men's T20 World Cup 2024**, published by Cricsheet under the **Open Data Commons Attribution License (ODC-By 1.0)**.
- **Tier B (Editorial News & Match Reviews)**: 5 comprehensive journalistic and tournament review documents (314 paragraphs, 13,650 words) from Wikimedia under the **Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA 4.0)** license.
- **Tier C (Ball-by-Ball Commentary)**: Commercial proprietary commentary streams (ESPNcricinfo, Cricbuzz) explicitly withhold scraping permissions under `robots.txt` and anti-crawler protections. In adherence to research ethics guidelines, commercial streams were not scraped, and the lack of authorized real-time commentary is documented as an honest research limitation.

The entire analytical pipeline was executed in strict dependency order:
$$\text{Ingestion} \longrightarrow \text{Entity Resolution} \longrightarrow \text{Dense Embeddings} \longrightarrow \text{Topic Clustering} \longrightarrow \text{Performance \& Attention} \longrightarrow \text{APDI Calculations}$$

All 100 automated unit and integration tests (`pytest tests/`) pass without failure, 9 of 9 frontend Vitest tests pass, and zero TypeScript errors exist.

---

## 2. Corpus Scope & Sampling Methodology

### 2.1 Bounded Sampling Criteria
A bounded sampling strategy was chosen to enable 100% manual audibility of scorecards, entity alignments, and statistical formulas:
1. **Tournament**: ICC Men's T20 World Cup 2024 (co-hosted in the West Indies and the United States, June 2024).
2. **Key Narrative Matches Selected**:
   - **Match 1 (`1415701`)**: Tournament opener — Canada vs United States (Grand Prairie, Texas).
   - **Match 11 (`1415711`)**: Historic upset — Pakistan vs United States (Tied match, Super Over victory for USA).
   - **Match 19 (`1415719`)**: Marquee clash — India vs Pakistan (New York, low-scoring thriller, India won by 6 runs).
   - **Match 42 (`1415742`)**: Super 8 — West Indies vs England (St Lucia).
   - **Match 44 (`1415744`)**: Super 8 — Bangladesh vs Australia (Antigua).
   - **Match 49 (`1415749`)**: Super 8 — USA vs England (Bridgetown, Chris Jordan hat-trick).
   - **Match 50 (`1415750`)**: Super 8 — West Indies vs South Africa (Antigua).
   - **Match 51 (`1415751`)**: Super 8 — India vs Australia (St Lucia, Rohit Sharma 92 off 41).
   - **Match 54 (`1415754`)**: Semi-Final 2 — India vs England (Guyana, India won by 68 runs).
   - **Match 55 (`1415755`)**: Final — India vs South Africa (Bridgetown, India won by 7 runs to become World Champions).

---

## 3. Legal and Ethical Compliance

### 3.1 Rights and Access Matrix
- **Cricsheet**: Ingested directly from official JSON format under ODC-By 1.0. Attribution given to Cricsheet.org.
- **Wikimedia / Wikipedia**: Harvested via official MediaWiki REST API (`https://en.wikipedia.org/api/rest_v1/page/html/`) under CC-BY-SA 4.0.
- **ESPNcricinfo & Cricbuzz**: Inspected `robots.txt` and Terms of Use. ESPNcricinfo explicitly disallows automated bot access (`Disallow: /rss/`). Cricbuzz live commentary is commercial IP. Bypassing CAPTCHAs, Cloudflare challenges, or rate limits was rejected.
- **Fair Use Disclaimer**: The platform explicitly rejects using `FairUse-ResearchExtraction` as a blanket license justification. Sources without open licenses were not ingested for full-text storage.

---

## 4. Ingestion & Quality Metrics

### 4.1 Ingestion Ledger

| Metric | Tier A (Cricsheet) | Tier B (Editorial) | Combined Corpus |
| :--- | :--- | :--- | :--- |
| **Files Scanned** | 10 | 5 | 15 |
| **Accepted Records** | 10 matches | 5 articles | 15 documents |
| **Rejected / Malformed** | 0 | 0 | 0 |
| **Deliveries Ingested** | 2,314 | N/A | 2,314 |
| **Paragraphs Segmented** | N/A | 314 | 314 |
| **Unique Teams** | 9 | N/A | 9 |
| **Unique Players** | 107 | N/A | 107 |
| **Execution Duration** | 1.82s | 10.98s | 12.80s |

### 4.2 Idempotency Verification
The ingestion script was executed twice consecutively against `data/cricket_intel.db`:
- **Run 1**: 10 matches, 2,314 deliveries, 5 articles, 314 paragraphs ingested.
- **Run 2**: 0 duplicate matches created, 0 duplicate deliveries created, 5 articles skipped (`Duplicate: content hash matches existing article`).
- **Relational Integrity**: 0 orphaned deliveries, 0 deliveries violating $total\_runs = batter\_runs + extra\_runs$, 0 articles missing paragraphs.

---

## 5. Cricket NLP & Entity Resolution Evaluation

### 5.1 Real-World Processing Output
- **Normalized Texts**: 314 paragraphs
- **Entity Mentions Extracted**: 683 mentions
- **Resolved Mentions**: 607 mentions (**88.9% resolution rate**)
- **Ambiguous Mentions**: 60 mentions (8.8% ambiguity rate)
- **Unresolved Mentions**: 16 mentions (2.3% unresolved rate)
- **Sentiment Baselines**: 588 baseline records (26 Positive, 538 Neutral, 24 Negative)

### 5.2 Gold-Set Quantitative Benchmark
A manually reviewed, separate gold set of 20 entity mentions (`data/evaluation/nlp_gold_set.json`) was evaluated using `scripts/evaluate_nlp_gold_set.py`:
- **Total Gold Mentions**: 20
- **Correctly Resolved**: 16
- **Ambiguous Detections**: 1 ("Sharma" without context marked Ambiguous)
- **Unresolved Count**: 3 ("Khan", "United States", "head")
- **Wrongly Resolved**: 0 (**Zero false entity associations**)
- **Resolution Accuracy**: **80.0%**
- **Ambiguity Detection Rate**: 5.0%
- **Entity Coverage**: 85.0%

> [!NOTE]
> The gold set of 20 samples is intended as a regression safeguard and sanity check. It demonstrates that the resolution engine conservatively prefers `AMBIGUOUS` or `UNRESOLVED` rather than generating false linkages.

---

## 6. Semantic Embeddings & Topic Discovery

### 6.1 Dense Embeddings
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Architecture**: 6-layer MiniLM dense transformer, 384 dimensions, L2-normalized
- **Texts Embedded**: 314 discrete paragraphs
- **Missing / Failed Embeddings**: 0
- **Vector Storage**: NumPy binary arrays in `data/cache/embeddings/`

### 6.2 Topic Discovery (K-Means, $k=3$)
- **Run ID**: `topic_run_20261024_080729_a23185`
- **Silhouette Score**: **0.214**
- **Davies-Bouldin Index**: **2.722**
- **Noise Ratio**: 0.0% (0 unassigned documents)
- **Clusters Discovered**:
  1. **Cluster 0 (120 docs)**: `india-pakistan-cup` — Keywords: *india, pakistan, cup, world, icc*
  2. **Cluster 1 (94 docs)**: `toss_elected-elected-won_toss` — Keywords: *toss elected, elected, won toss, toss, field*
  3. **Cluster 2 (100 docs)**: `2024-retrieved-squad` — Keywords: *2024, retrieved, squad, t20, world*

---

## 7. Media Attention, Performance & APDI Audit

### 7.1 Objective Performance Highlights
- **India**: 4/4 wins (100% win rate), Raw Composite = **175.00**
- **JJ Bumrah**: 14.4 overs, 73 runs conceded, 8 wickets, 43 dot balls, Economy = 4.98, Raw Composite = **268.59**
- **Virat Kohli**: 89 runs, 76 balls faced, 7 fours, 3 sixes, Strike Rate = 117.11, Raw Composite = **110.56**
- **Rohit Sharma**: 92 runs in match 51, Strike Rate = 164.71, Raw Composite = **152.00**

### 7.2 Independent APDI Calculation Verification
The Attention-to-Performance Discrepancy Index was independently hand-audited using `scripts/audit_apdi_calculation.py`:
$$\text{APDI} = \text{NormAttention} - \text{NormPerformance}$$

| Entity | Role | Normalized Attention | Normalized Performance | Actual APDI | Expected APDI | Discrepancy Category | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Pakistan** | Team | 0.8333 | 0.3333 | **+0.5000** | +0.5000 | `OVER_ATTENDED` | VALID |
| **Bangladesh** | Team | 0.3333 | 0.0000 | **+0.3333** | +0.3333 | `OVER_ATTENDED` | VALID |
| **India** | Team | 1.0000 | 1.0000 | **0.0000** | 0.0000 | `BALANCED` | VALID |
| **Canada** | Team | 0.1667 | 0.1667 | **0.0000** | 0.0000 | `BALANCED` | VALID |
| **England** | Team | 0.6667 | 0.8333 | **-0.1666** | -0.1666 | `BALANCED` | VALID |
| **Australia** | Team | 0.5000 | 0.6667 | **-0.1667** | -0.1667 | `BALANCED` | VALID |
| **United States** | Team | 0.0000 | 0.5000 | **-0.5000** | -0.5000 | `UNDER_ATTENDED` | VALID |
| **Mustafizur Rahman** | Bowler | 0.6667 | 0.0000 | **+0.6667** | +0.6667 | `OVER_ATTENDED` | VALID |
| **Kuldeep Yadav** | Bowler | 0.0000 | 0.6667 | **-0.6667** | -0.6667 | `UNDER_ATTENDED` | VALID |
| **Mohammad Rizwan** | Batter | 0.0000 | 1.0000 | **-1.0000** | -1.0000 | `UNDER_ATTENDED` | VALID |

### 7.3 Insufficient Data Safeguard
- Entities with fewer than 3 observations in their role cohort or 0 editorial mentions are classified as `INSUFFICIENT_DATA`.
- **103 player entities** appropriately remain `INSUFFICIENT_DATA` with `apdi_value = NULL`.
- No speculative, fabricated, or interpolated scores were generated.

---

## 8. End-to-End API and Dashboard Verification

### 8.1 FastAPI Backend Status
The backend server was executed at `http://127.0.0.1:8000`:
- `/health` — `200 OK` (status: "healthy", database connected)
- `/api/v1/matches` — `200 OK` (10 real matches returned with innings totals and winners)
- `/api/v1/players` — `200 OK` (107 real players returned)
- `/api/v1/articles` — `200 OK` (5 real CC-BY-SA articles returned)
- `/api/v1/analytics/overview` — `200 OK` (real tournament statistics)
- `/api/v1/analytics/apdi` — `200 OK` (real computed APDI records)
- `/api/v1/topics` — `200 OK` (3 semantic topic clusters)
- `/api/v1/entities` — `200 OK` (683 extracted entity mentions)

### 8.2 Frontend Dashboard Verification
The React/Vite dashboard was executed at `http://127.0.0.1:5173` and audited using the automated browser subagent:
- **Overview**: Real API-driven metric cards (Matches: 10, Deliveries: 2,314, Articles: 5, APDI Records: 162).
- **Matches Explorer**: Interactive directory showing real 2024 ICC T20 World Cup matches (IND vs SOU Final, IND vs PAK, PAK vs USA, etc.).
- **APDI Explorer**: Displays genuine discrepancy categories, percentile comparisons, and `INSUFFICIENT_DATA` badges without fake fallbacks.
- **Topics & Narratives**: Displays unsupervised semantic topic clusters (`india-pakistan-cup`, `toss_elected...`, `2024-retrieved-squad`) and chronological timeline snapshots.

---

## 9. Known Biases and Research Limitations

1. **Tournament Scope**: The corpus is bounded to 10 selected matches from the 2024 ICC Men's T20 World Cup. Results reflect this specific tournament sample and cannot be generalized to all historical T20 cricket.
2. **Commentary Gap**: Due to commercial licensing restrictions, live proprietary ball-by-ball commentary feeds were not scraped. Ball-by-ball delivery facts are sourced strictly from Cricsheet.
3. **Editorial Source Diversity**: Editorial texts originate from Creative Commons Wikipedia articles. While neutral and high in factual density, they exhibit different stylistic patterns from tabloid sensationalism or live match blogging.
4. **Descriptive Metric**: APDI measures observed statistical discrepancies between media frequency and objective match performance. It does not prove intentional media bias or causal favoritism.
