# Project Blueprint: T20 Cricket Intelligence Platform

## 1. Executive Summary & Core Research Vision

The **T20 Cricket Intelligence Platform** is an evidence-driven, explainable sports analytics and natural language processing (NLP) research system focused on the Men's ICC T20 World Cup.

While existing cricket analytics platforms focus primarily on structured ball-by-ball performance metrics (wagon wheels, run rates, win probabilities) or isolated text scrapers, this platform bridges the gap between **unstructured cricket media (news reports, post-match analysis, tactical editorials, ball-by-ball written commentary)** and **structured match event evidence (deliveries, wickets, phases, scorecards from open datasets like Cricsheet)**.

### Core Research Question
> **How can unstructured cricket journalism and commentary be systematically connected to structured match evidence to discover, explain, and evaluate narratives surrounding a T20 World Cup tournament?**

---

## 2. Primary Research Objectives & Hypotheses

The platform approaches narrative discovery as a series of measurable scientific hypotheses rather than pre-assumed outcomes:

1. **Unsupervised Topic Discovery**:
   - *Hypothesis*: Recurring cricket tournament themes (e.g., death-overs bowling execution, top-order powerplay collapses, spin effectiveness on slow tracks, selection and injury dilemmas) can be discovered using topic modeling without manually pre-defining rigid taxonomy labels.
2. **Semantic Equivalence Across Disparate Vocabulary**:
   - *Hypothesis*: Dense semantic representations (sentence embeddings) can cluster articles reporting on the same event or theme even when distinct publishers use completely different vocabularies (e.g., "bludgeoned at the death" vs. "expensive final overs concession").
3. **Commentary vs. Journalism Alignment**:
   - *Hypothesis*: Micro-commentary written in real time (high temporal resolution, short burst texts) can be mapped to macro-journalistic retrospectives (narrative-heavy, reflective) through shared entity-time-phase alignment.
4. **Cross-Source Event Grounding**:
   - *Hypothesis*: Specific media assertions (e.g., "the 18th over changed the entire game") can be linked with measurable precision and recall to exact match delivery windows (e.g., Over 17.1–17.6) and structured win-probability/run-rate shifts.
5. **Narrative & Sentiment Evolution**:
   - *Hypothesis*: Media sentiment towards players and tactical approaches exhibits quantifiable state shifts triggered by pivotal match turning points, with measurable lag and publisher-specific framing.
6. **Media Attention vs. On-Field Reality**:
   - *Hypothesis*: Disproportional media attention (hype/criticism) exists relative to objective statistical contribution (runs above average, impact wickets, economy in pressure overs), which can be quantified through attention-to-performance index ratios.
7. **Cross-Publisher Framing**:
   - *Hypothesis*: Different regional or editorial publishers exhibit distinct thematic framing for the identical match event without requiring subjective or ungrounded claims of bias.
8. **Traceability and Explainability**:
   - *Hypothesis*: Every summary, cluster label, and analytical claim produced by the system can provide direct back-pointers to specific canonical delivery IDs and source article paragraph citations.

---

## 3. High-Level System Layers

```
+-----------------------------------------------------------------------------------------+
|                                06. PRESENTATION & EXPLORER                              |
|   Interactive React/TypeScript Dashboard | Narrative Explorer | Match Delivery Timeline |
|   FastAPI Analytical Query Service | Evidence Provenance Inspector                      |
+-----------------------------------------------------------------------------------------+
                                           ^
                                           | Query & Explainability APIs
+-----------------------------------------------------------------------------------------+
|                         05. CLUSTERING & CROSS-SOURCE REASONING                         |
|   TF-IDF / Sentence Transformers / HDBSCAN / BERTopic Experiments                       |
|   Media-to-Match Event Alignment Engine | Narrative Dynamics & Sentiment Drift          |
|   Attention vs Performance Metrics Engine                                               |
+-----------------------------------------------------------------------------------------+
            ^                                                           ^
            | Enriched Vectors & Entities                               | Match Sequences
+---------------------------------------+   +---------------------------------------------+
|          04A. CRICKET NLP             |   |            04B. MATCH ANALYTICS             |
| Text Cleaning & Domain Lexicon        |   | Ball-by-Ball Parsing & Phase Aggregations   |
| Rule-Based & NER Extraction           |   | Pressure Indexes, Partnerships, Run Rates   |
| Alias & Player Entity Resolution      |   | Cricsheet Event Segmentation                |
| Aspect & Tournament Sentiment         |   | Turning-Point Detection                     |
+---------------------------------------+   +---------------------------------------------+
            ^                                                           ^
            | Structured Clean Text                                     | Normal Deliveries
+-----------------------------------------------------------------------------------------+
|                            03. CANONICAL CRICKET DATA LAYER                             |
|   PostgreSQL / SQLite Relational Models & Reproducible Parquet / JSONL Archives         |
|   Articles | Commentary Passages | Deliveries | Innings | Matches | Players | Teams     |
|   Deterministic Content Hashing & Full Provenance Lineage Records                       |
+-----------------------------------------------------------------------------------------+
            ^                                                           ^
            | Extracted Records                                         | Parsed Feeds
+-----------------------------------------------------------------------------------------+
|                        02. EXTRACTION, NORMALIZATION & VALIDATION                       |
|   Trafilatura HTML Extraction | BeautifulSoup Fallbacks | Schema Pydantic Validation   |
|   Deduplication & Content Normalization | Timezone Canonicalization (UTC)               |
+-----------------------------------------------------------------------------------------+
            ^                                                           ^
            | Raw HTML / JSON Payloads                                  | Structured Files
+-----------------------------------------------------------------------------------------+
|                         01. SOURCE REGISTRY & ADAPTER FRAMEWORK                         |
|   Permitted Scrapers (Robots.txt verified) | Authorized APIs | Cricsheet Open Datasets  |
|   Rate Limiting (Token Bucket) | Backoff Retries | Idempotent Ingestion Checkpoints     |
+-----------------------------------------------------------------------------------------+
```

---

## 4. Key Architectural & Research Principles

1. **Local-First & Resource Efficient**:
   The primary system must execute predictably on standard developer hardware without mandatory cloud clusters, distributed streaming brokers, or hosted vector databases. SQLite/PostgreSQL, local Parquet/JSONL, and local transformer inference (quantized where suitable) form the foundation.

2. **Permissible, Responsible Ingestion**:
   Strict adherence to `robots.txt`, publisher terms of service, rate limits, and copyright restrictions. No paywall bypassing, CAPTCHA defeating, or credential forging. Open data (e.g., Cricsheet) is used as the backbone of match facts.

3. **Modularity with Stable Interfaces**:
   Every layer communicates via typed Pydantic models. Adapters can be added or replaced without changing NLP or clustering logic.

4. **Evidence Grounding (No Hallucinated Narratives)**:
   Every generated insight or cluster must cite underlying canonical delivery IDs, match dates, player IDs, and verbatim article excerpts.

5. **Empirical Benchmarking Over Assumption**:
   Model choices (TF-IDF vs. embeddings, K-Means vs. HDBSCAN vs. BERTopic) are judged through rigorous comparative experiments on identical evaluation test sets.

---

## 5. Associated Planning & Design Documents

- [REQUIREMENTS.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/REQUIREMENTS.md) — Functional and non-functional engineering specifications.
- [ARCHITECTURE.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/ARCHITECTURE.md) — Detailed component architecture, data flows, and module design.
- [DATA_MODEL.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/DATA_MODEL.md) — Canonical schemas, relational DDL, entity dictionaries, and storage layouts.
- [SOURCE_REGISTER.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SOURCE_REGISTER.md) — Provenance ledger of data sources, open-source repositories, and licenses.
- [REPOSITORY_AUDITS.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/REPOSITORY_AUDITS.md) — Systematic evaluation criteria for candidate upstream repositories.
- [RESEARCH_PLAN.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/RESEARCH_PLAN.md) — Scientific hypotheses, baseline pipelines, and experimental setups.
- [EVALUATION_PLAN.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/EVALUATION_PLAN.md) — Metrics, gold-standard test sets, cluster coherence, and alignment benchmarks.
- [SECURITY_AND_LICENSING.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SECURITY_AND_LICENSING.md) — Intellectual property, fair use, rate-limits, and credential handling.
- [IMPLEMENTATION_ROADMAP.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/IMPLEMENTATION_ROADMAP.md) — Phased milestone delivery with strict completion gates.
- [DECISIONS.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/DECISIONS.md) — Architecture Decision Records (ADRs) tracking design alternatives and trade-offs.
- [SESSION_JOURNAL.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SESSION_JOURNAL.md) — Chronological developer journal tracking daily steps, tests, and findings.
