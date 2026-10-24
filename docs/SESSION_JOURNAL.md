# Engineering Session Journal: T20 Cricket Intelligence Platform

## Session 01: Project Initialization & Architectural Specifications
- **Date**: 2026-10-20
- **Lead Role**: Senior Data Engineer & Project Architect
- **Current Phase**: Phase 0 (Requirements & Blueprint)
- **Status**: COMPLETED

---

### 1. Context & Objective
The goal of this initialization session was to inspect the workspace, establish the project isolation rules, and build out the complete architectural, research, data modeling, evaluation, and security documentation suite before cloning or integrating any candidate open-source repositories.

---

### 2. Workspace Inspection & Environmental State
- **Workspace Path**: `c:\Users\Ritesh Panda\OneDrive\Desktop\atsma_lab`
- **Initial Inspection Result**: Empty directory. No pre-existing files, submodules, or dirty git states.
- **Operating Environment**: Windows PowerShell, Python runtime available, local-first target.

---

### 3. Actions Taken & Deliverables Created

1. **Repository Isolation & Hygiene**:
   - Created `.gitignore` excluding `research_sources/` (quarantined external clones), `data/` (raw and processed data), `models/cache/`, virtual environments, and secrets.
   - Created `.env.example` defining environment variables for local-first execution (SQLite/PostgreSQL URL, rate limits, crawler user-agent, embedding model identifiers).

2. **Core Architectural & Research Documentation Suite** (`docs/`):
   - [PROJECT_BLUEPRINT.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/PROJECT_BLUEPRINT.md): Platform vision, primary research questions, multi-layer architecture, and guiding principles.
   - [REQUIREMENTS.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/REQUIREMENTS.md): Functional requirements (FR-A through FR-L) and Non-Functional Requirements (NFR-1 through NFR-6).
   - [ARCHITECTURE.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/ARCHITECTURE.md): Component decomposition, Mermaid flowcharts, module interfaces, and directory layout.
   - [DATA_MODEL.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/DATA_MODEL.md): Canonical entity specifications (Matches, Innings, Deliveries, Players, Articles, Commentary, EntityMentions, TopicClusters, EventAlignments).
   - [SOURCE_REGISTER.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SOURCE_REGISTER.md): Primary data source inventory (Cricsheet, ESPNcricinfo, Cricbuzz, Wisden) and upstream repository ledger template.
   - [REPOSITORY_AUDITS.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/REPOSITORY_AUDITS.md): 5-pillar audit rubric (Licensing, Security, Architecture, Code Quality, Maintenance) and 4-way decision framework (`REUSE`, `ADAPT`, `REFERENCE ONLY`, `REJECT`).
   - [RESEARCH_PLAN.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/RESEARCH_PLAN.md): Experimental model matrix (TF-IDF vs. Dense Embeddings vs. HDBSCAN vs. BERTopic), 2-stage corpus segmentation, and alignment heuristic formulation.
   - [EVALUATION_PLAN.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/EVALUATION_PLAN.md): Quantitative metrics (Silhouette, Davies-Bouldin, Coherence, Outlier rate, Precision/Recall/MRR) and qualitative protocols (word/topic intrusion tests).
   - [SECURITY_AND_LICENSING.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SECURITY_AND_LICENSING.md): Legal constraints, robots.txt compliance, copyright/fair use policies, and secret handling.
   - [IMPLEMENTATION_ROADMAP.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/IMPLEMENTATION_ROADMAP.md): 9-phase milestone execution plan with verifiable completion gates.
   - [DECISIONS.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/DECISIONS.md): Formal Architecture Decision Records (ADR-001 through ADR-005) and unresolved trade-off evaluations (U-01 through U-03).
   - [SESSION_JOURNAL.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SESSION_JOURNAL.md): This tracking log.

---

### 4. Verified Decisions & Principles Established
- **Isolation Policy**: Third-party repositories will be cloned into `research_sources/` and audited without executing arbitrary scripts.
- **Match Fact Grounding**: Cricsheet open data is established as the canonical factual foundation for matches and deliveries.
- **Empirical Rigor**: Multiple topic models will be benchmarked on identical evaluation test sets rather than assuming BERTopic or K-Means is unconditionally superior.
- **Explainability**: Every media-to-match link will store verifiable evidence (entities, timestamps, commentary window vectors).

---

### 5. Unresolved Questions & Trade-offs
1. **Relational Engine Choice**: SQLite with WAL mode recommended for initial zero-setup local speed; PostgreSQL supported via connection string when concurrent crawling writes begin.
2. **Dashboard UI Technology**: Proceeding with React + TypeScript + Vite + Tailwind CSS for a premium sports intelligence experience; backend served via FastAPI.
3. **Repository URL Batch**: Awaiting user input of candidate open-source repository URLs to commence Phase 1.

---

### 6. Next Immediate Action
Proceed to Phase 1: Ingest candidate repository URLs, audit codebases, and establish reuse decisions.

---

## Session 02: Candidate Repository Ingestion, 5-Pillar Audits & Integration Architecture
- **Date**: 2026-10-20
- **Lead Role**: Senior Data Engineer & Open-Source Integration Architect
- **Current Phase**: Phase 1 (Repository Audits & Reuse Decisions)
- **Status**: COMPLETED

---

### 1. Context & Objective
The user provided a curated batch of 9 candidate open-source cricket analytics and NLP projects. The objective was to quarantine-clone the repositories into `research_sources/`, perform an exhaustive 5-pillar technical and licensing audit, evaluate overlapping functionalities, identify critical research gaps, and design a single, cohesive integration architecture.

---

### 2. Candidate Repositories Audited & Cloned
1. `ZainZoy/NLP-project` (`76578b46787acf6408d64b0d49c233e27de029c0`) -> **ADAPT** (18/25)
2. `princyhareshbhai1530/T20-Commentary-Analysis` (`af64837c57b3163c2e181e76cf4b82683f17cc83`) -> **REFERENCE ONLY** (9/25)
3. `HalcyonVector/Cricket-Intelligence-Lab` (`57be3daf1f92bdcca55eb8ce95fbcd1c1a3409f9`) -> **ADAPT** (19/25)
4. `vinaybale-collab/cricket-analytics-web` (`4cffafabdf0eef30db05cc6c41134221f26f2d97`) -> **REFERENCE ONLY** (12/25)
5. `Anurag9557/cricket-iq` (`8c67a120b85ada7855bfaeaa161951277ded1781`) -> **REUSE / ADAPT** (23/25, MIT License)
6. `ShrinathSontakke/Cricket-Data-Analytics` (`1448b257bc935541b8d48edfdcb5b17ea7171d02`) -> **REJECT** (6/25)
7. `Paul-ans-typ/Analysis-of-Cricket-Commentary` (`e580d8faa0d37b463ab26677d22aded5e4099d77`) -> **REJECT** (6/25)
8. `sst-cloud-solutions/h25-sports` (`47bbce76226603aa1b6a6b4bf9fa21241338d6a3`) -> **REJECT** (7/25, License Blocker: UNLICENSED private)
9. `SRIHARI18V/CRICKET-RAG-CHATBOT` (`f94d1b9668c8ca47ecb484c7ad5d03635b74f1ae`) -> **REFERENCE ONLY** (13/25)

---

### 3. Key Findings & Licensing Realities
- **Software Licensing**: Only `Anurag9557/cricket-iq` carries an explicit, verified MIT license. `sst-cloud-solutions/h25-sports` carries an explicit `UNLICENSED` private notice prohibiting code reuse. The other 7 repositories omit formal root license files, requiring an **ADAPT** / **REFERENCE ONLY** strategy (clean-room re-implementation of mathematical formulas, regex grammar, and heuristics within canonical Pydantic schemas) to avoid copyright infringement.
- **Critical Architectural Discovery**: `HalcyonVector` demonstrated that Cricbuzz public pages inline structured JSON inside Next.js streaming payloads (`self.__next_f.push([...])`), enabling ultra-fast, polite HTTP extraction without Playwright, Selenium, or headless browser bloat.
- **Analytics Benchmark**: `Anurag9557/cricket-iq` provides a vectorized Polars chase-state builder and LightGBM win-probability engine that outperforms traditional pandas scripts in both speed and mathematical rigor.

---

### 4. Gaps Identified (Original Capabilities to Build)
None of the 9 candidate repositories address:
1. Ingestion of journalistic news articles (previews, reviews, tactical essays).
2. Cross-source media-to-match delivery event alignment.
3. Unsupervised topic modeling benchmarks (TF-IDF vs. Embeddings vs. HDBSCAN vs. BERTopic).
4. Cricket-specific named entity resolution with nickname gazetteers and squad-context disambiguation.
5. Media attention share vs. statistical performance ratios ($APR$).
6. Clickable interactive provenance tracing linking insights to source paragraphs and delivery IDs.

---

### 5. Deliverables Produced & Updated
- Updated [docs/REPOSITORY_AUDITS.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/REPOSITORY_AUDITS.md) with complete 5-pillar audit cards.
- Updated [docs/SOURCE_REGISTER.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SOURCE_REGISTER.md) with exact commit hashes, licenses, and attribution requirements.
- Created [docs/REUSE_DECISIONS.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/REUSE_DECISIONS.md) detailing comparative capability matrix and best implementations.
- Created [docs/INTEGRATION_ARCHITECTURE.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/INTEGRATION_ARCHITECTURE.md) defining the unified, local-first integration architecture.

---

### 6. Next Checkpoint & Action
Proceed to **Phase 2: Canonical Schemas, Storage Setup & Source Adapters**.

---

## Session 03: Canonical Schemas, Storage Layer & Initial Source Adapters
- **Date**: 2026-10-20
- **Lead Role**: Senior Data Engineer & Open-Source Integration Architect
- **Current Phase**: Phase 2 (Schemas, Storage & Adapters)
- **Status**: COMPLETED

---

### 1. Context & Objective
The goal was to implement a tested, local-first data foundation supporting structured match deliveries from Cricsheet, ball-by-ball natural language commentary, and permitted cricket news articles, grounded in canonical entities and strict schema validation.

---

### 2. Actions Taken & Components Implemented

1. **Canonical Pydantic v2 Models** ([`src/models/canonical.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/models/canonical.py)):
   - Implemented 10 versioned models: `SourceRecord`, `IngestionRun`, `TeamRecord`, `PlayerRecord`, `DeliveryRecord`, `MatchRecord`, `CommentaryRecord`, `ArticleRecord`, `ArticleParagraphRecord`, `EventAlignmentRecord`.
   - Built strict model validators: total runs cross-check (`total_runs == batter_runs + extra_runs`), required dismissed player validation on wickets, and 64-char SHA-256 fingerprint verification.

2. **Local-First Storage Layer** ([`src/storage/`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/storage)):
   - [`SQLiteStorageManager`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/storage/sqlite_manager.py): WAL-mode transactional persistence for metadata, provenance audit trails, and relational tables. Enforces idempotent ingestion and article deduplication over canonical URLs and raw content hashes.
   - [`ParquetStorageManager`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/storage/parquet_manager.py): Columnar Apache Parquet tables for deliveries and matches with atomic writes (`.tmp.parquet` -> `.parquet`).

3. **Source Adapters** ([`src/adapters/`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/adapters)):
   - [`BaseSourceAdapter`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/adapters/base.py): Base adapter enforcing polite rate limits, exponential backoff retries, and robots.txt parsing.
   - [`CricsheetAdapter`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/adapters/cricsheet_adapter.py): Ingests official Cricsheet 1.1.0/1.2.0 JSON, resolves player registry IDs, assigns match phases (`powerplay`, `middle`, `death`), and performs score reconciliation.
   - [`CommentaryAdapter`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/adapters/commentary_adapter.py): Deterministic line grammar parser with event milestone tagger (`FOUR`, `SIX`, `WICKET`, `DRS`, `FIFTY`) and Cricbuzz Next.js streaming JSON extractor.
   - [`NewsArticleAdapter`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/adapters/news_adapter.py): Article extractor using Trafilatura with BeautifulSoup4 DOM fallback and paragraph segmentation.

4. **Testing Suite** ([`tests/`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/tests)):
   - Created test fixtures under `tests/fixtures/`: `cricsheet_sample_t20.json`, `cricsheet_malformed.json`, `sample_commentary.txt`, `sample_article.html`.
   - Created `pytest.ini` isolating test runs from `research_sources/`.
   - Executed 15 test cases across 6 test modules with **100% passing rate** (`15 passed in 5.30s`).

---

### 3. Test Execution Results
```
tests/test_commentary_adapter.py::test_parse_commentary_text_lines PASSED [  6%]
tests/test_commentary_adapter.py::test_cricbuzz_nextjs_payload_parsing PASSED [ 13%]
tests/test_cricsheet_adapter.py::test_parse_valid_cricsheet_fixture PASSED [ 20%]
tests/test_cricsheet_adapter.py::test_parse_malformed_cricsheet_fixture PASSED [ 26%]
tests/test_integration.py::test_full_ingestion_and_provenance_pipeline PASSED [ 33%]
tests/test_news_adapter.py::test_parse_sample_news_article PASSED        [ 40%]
tests/test_schemas.py::test_team_record_validation PASSED                [ 46%]
tests/test_schemas.py::test_player_record_creation PASSED                [ 53%]
tests/test_schemas.py::test_delivery_record_validation PASSED            [ 60%]
tests/test_schemas.py::test_source_record_sha256 PASSED                  [ 66%]
tests/test_schemas.py::test_article_record_id_generation PASSED          [ 73%]
tests/test_storage.py::test_sqlite_provenance_deduplication PASSED       [ 80%]
tests/test_storage.py::test_sqlite_match_and_delivery_roundtrip PASSED   [ 86%]
tests/test_storage.py::test_sqlite_article_deduplication PASSED          [ 93%]
tests/test_storage.py::test_parquet_storage_roundtrip PASSED             [100%]
======================= 15 passed, 2 warnings in 5.30s ========================
```

---

### 4. Known Format Limitations & Data Gaps Documented
1. **Cricsheet Registry Gaps**: Occasionally older Cricsheet files omit `info.registry.people` or player hand/bowling style. Our adapter falls back cleanly to deterministic name slugs (`player_{clean_name}`) and leaves styles nullable.
2. **Commentary Delivery Indexing**: Live commentary liveblogs often do not report exact legal delivery indexes when multiple wides or no-balls occur consecutively. We resolve this by indexing sequentially per over (`deliv_ov{over}_b{idx}`).
3. **News Article Byline Heterogeneity**: Some publishers use syndicated wire tags or omit bylines. Trafilatura and BS4 fallbacks extract metadata from OpenGraph and HTML5 `<time>` tags, storing `None` when unavailable rather than fabricating.

---

### 5. Next Checkpoint & Action
Proceed to **Phase 3: Acquisition, Extraction Pipeline & Idempotent Ingestion**.

---

## Session 04: Acquisition Pipeline, Crawling, Discovery & Idempotent Ingestion
- **Date**: 2026-10-20
- **Lead Role**: Senior Data Engineer & Open-Source Integration Architect
- **Current Phase**: Phase 3 (Acquisition Pipeline & Idempotent Ingestion)
- **Status**: COMPLETED

---

### 1. Context & Objective
The goal of Phase 3 was to build a reliable, restartable, configuration-driven acquisition pipeline that discovers permitted cricket data sources across three independent tracks (A: Cricsheet structured data, B: ball-by-ball commentary, C: cricket journalism & reviews), normalizes and validates them through the existing adapters, and persists them idempotently without duplicates.

---

### 2. Components Implemented & Extended

1. **Source Registry & Configuration** ([`src/pipeline/config.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/pipeline/config.py), [`config/sources.yaml`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/config/sources.yaml)):
   - Strongly-typed Pydantic model `SourceConfig` with fields for `source_id`, `category` (`structured_data`, `commentary`, `news`), `base_url`, `discovery_endpoints`, `adapter_id`, `rate_limit_rps`, `request_timeout_sec`, `max_retries`, `max_response_bytes`, `supported_content_types`, `retention_policy`, `license_tag`, `licence_notes`, and `allowed_domains`.
   - Populated profiles for Cricsheet, ESPNcricinfo, Cricbuzz, and Wisden.

2. **URL Normalizer & Discovery Engine** ([`src/pipeline/url_normalizer.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/pipeline/url_normalizer.py), [`src/pipeline/discovery.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/pipeline/discovery.py)):
   - Canonical URL normalizer stripping marketing/tracking query parameters (`utm_*`, `fbclid`, `ref`) and structural fragments (`#comments`) while preserving resource-distinguishing parameters (`match_id`, `story_id`).
   - Parsers for RSS 2.0/Atom XML feeds, XML sitemaps, sitemap indices, Cricsheet download directories, and approved HTML listing pages.
   - Pre-download deduplication across discovery endpoints.

3. **Responsible Fetcher** ([`src/pipeline/fetcher.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/pipeline/fetcher.py)):
   - Polite HTTP fetcher with explicit connect/read timeouts and inter-request rate limiting.
   - Bounded retries with exponential backoff and jitter on 5xx responses.
   - HTTP 429 `Retry-After` parsing (supporting seconds and RFC 2822 dates).
   - Conditional requests via `ETag` (`If-None-Match`) and `Last-Modified` (`If-Modified-Since`), returning HTTP 304.
   - Streaming response size enforcement (aborting payloads exceeding `max_response_bytes`).
   - Redirect chain domain verification (`DisallowedRedirectError`).
   - Per-domain cached `robots.txt` enforcement.

4. **Acquisition State Machine & Storage Extensions** ([`src/pipeline/state_machine.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/pipeline/state_machine.py), [`src/storage/sqlite_manager.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/storage/sqlite_manager.py)):
   - Explicit 9-state resource lifecycle: `DISCOVERED`, `QUEUED`, `FETCHED`, `PARSED`, `VALIDATED`, `INGESTED`, `SKIPPED`, `RETRY_PENDING`, `FAILED`.
   - Transition validation raising `IllegalStateTransitionError` on illegal hops.
   - SQLite tables: `discovered_urls` and `article_revisions` (schema version upgraded to 2).
   - Idempotent article upserts: exact hash matches skipped; content revisions stored in `article_revisions` while preserving canonical `article_id`.
   - Atomic replacement of deliveries for revised matches (`replace_deliveries_for_match`).

5. **Entity & Match Linking** ([`src/pipeline/entity_linker.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/pipeline/entity_linker.py)):
   - Multi-signal heuristic linker connecting unstructured text to ground-truth matches using team co-occurrence (+0.45), date proximity (+0.15 to +0.35), tournament mention (+0.10 to +0.15), and venue (+0.05 to +0.10).
   - Confidence threshold gate ($\ge 0.65$) and ambiguity margin ($\ge 0.15$), leaving ambiguous records unresolved to prevent false claims.

6. **Acquisition Orchestrator & CLI** ([`src/pipeline/orchestrator.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/pipeline/orchestrator.py), [`src/pipeline/cli.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/pipeline/cli.py)):
   - Complete lifecycle runner with transactional error isolation and dry-run mode.
   - CLI commands: `list`, `run`, `stats`, `inspect-failed`, `validate`, and guarded `smoke-test` (requiring `--confirm-live`).

---

### 3. Test Verification & Smoke Test Results
- Extended test suite with 20 new tests in [`tests/test_pipeline.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/tests/test_pipeline.py) covering URL normalization, RSS/sitemap parsing, retry/backoff, 429 handling, content-type checks, redirect security, deduplication, legitimate updates, transaction rollback, and entity linking.
- **Total Test Results**: **35 passed, 0 failed in 6.41s** across 7 test modules.
- **Live Smoke Test Outcome**:
  - `cricsheet` endpoint (`https://cricsheet.org/matches/`) tested live with explicit `--confirm-live`.
  - Result: HTTP 200, Robots.txt check ALLOWED, 16,215 bytes received in 0.24s.
  - Smoke test guard successfully blocked unconfirmed live invocations.

---

### 4. Documentation Deliverables
- [`docs/ACQUISITION_PIPELINE.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/ACQUISITION_PIPELINE.md): Pipeline architecture, state machine, deduplication, entity linking, and CLI operations.
- [`docs/SOURCE_CONFIGURATION.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SOURCE_CONFIGURATION.md): Source registry schema, source parameters, rate limits, and retention policies.
- [`docs/DATA_QUALITY.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/DATA_QUALITY.md): Quality dimensions, invariants, metrics, failure analysis, and honest coverage reporting.
- [`docs/SECURITY_AND_LICENSING.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SECURITY_AND_LICENSING.md): Updated with Section 5 (Pipeline Safeguards & Retention Controls).

---

### 5. Next Checkpoint & Action
Proceed to **Phase 4: Text Processing, Cricket NER & Entity Resolution**.

---

## Session 05: Phase 4 Plan — Text Processing, Cricket NER, Entity Resolution & Sentiment Baselines
- **Date**: 2026-10-20
- **Lead Role**: Senior NLP/ML Researcher & Data Engineer
- **Current Phase**: Phase 4 (Text Processing & NLP Foundations)
- **Status**: COMPLETED

---

### 1. Phase 4 Objectives Achieved
1. Implemented a modular, reproducible, CPU-first NLP processing layer under `src/nlp/`.
2. Built cricket-aware text cleaning and normalization strictly preserving cricket notations (`19.4`, `182/5`, `82*`, `DRS`, `LBW`, `not out`, negation).
3. Built a deterministic cricket tokenizer supporting overs, scores, player initials, acronyms, compound phrases, and cricket expressions.
4. Established an auditable cricket gazetteer (`config/cricket_gazetteer.yaml`) enriched dynamically from canonical database records (`teams`, `players`).
5. Implemented hybrid named entity recognition (NER) for players, teams, tournaments, and venues with boundary-aware matching and exact character offsets.
6. Built multi-signal entity resolution separating candidate generation from ranking, with configurable confidence thresholds ($\ge 0.70$) and ambiguity margins ($\ge 0.15$), cleanly preserving ambiguous cases without false links.
7. Implemented interpretable, entity-targeted sentiment and performance framing baselines separating general tone, event outcome polarity, and player/team framing (including bowler/batter polarity inversion).
8. Extended SQLite storage with Schema Version 3 migration (`normalized_texts`, `entity_mentions`, `entity_resolutions`, `sentiment_baselines`, `nlp_runs`) ensuring idempotent writes and transaction rollback.
9. Integrated with existing CLI (`process-text`, `nlp-stats`, `nlp-validate`, `resolve-entity` with optional `--context`).
10. Built deterministic labelled fixtures and test suites evaluating precision, recall, resolution ambiguity, and sentiment baselines.

---

### 2. Modules Created & Extended

- [`src/nlp/schemas.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/nlp/schemas.py): Canonical Pydantic v2 schemas and enums (`EntityType`, `ResolutionStatus`, `SentimentLabel`).
- [`src/nlp/text_cleaner.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/nlp/text_cleaner.py): `CricketTextCleaner` handling HTML unescaping, Unicode standardisation, and journalistic boilerplate removal while preserving cricket numbers and punctuation.
- [`src/nlp/cricket_tokenizer.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/nlp/cricket_tokenizer.py): `CricketTokenizer` handling overs (`19.4`), scores (`182/5`, `82*`), compound phrases (`not out`, `death overs`), and acronyms (`T20`, `T20I`, `DRS`, `LBW`).
- [`config/cricket_gazetteer.yaml`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/config/cricket_gazetteer.yaml): Seed gazetteer catalog with ambiguity tags.
- [`src/nlp/gazetteer.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/nlp/gazetteer.py): `CricketGazetteer` YAML loading, SQLite synchronization, and length-prioritized regex compilation.
- [`src/nlp/ner.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/nlp/ner.py): `CricketNER` boundary-aware entity extractor with longest-span priority.
- [`src/nlp/entity_resolver.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/nlp/entity_resolver.py): `EntityResolver` multi-signal candidate ranker with team context cues (+0.35) and conservative thresholds.
- [`src/nlp/sentiment.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/nlp/sentiment.py): `CricketSentimentBaseline` separating general sentiment, event polarity, and entity framing.
- [`src/nlp/processing_pipeline.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/nlp/processing_pipeline.py): `NLPPipeline` end-to-end processing orchestrator with SQLite persistence.
- [`src/nlp/evaluation.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/nlp/evaluation.py): Quantitative evaluation engine for precision, recall, F1, and ambiguity rates.
- [`src/storage/sqlite_manager.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/storage/sqlite_manager.py): Upgraded to `SCHEMA_VERSION = 3` with DDL and transactional upsert methods.
- [`src/pipeline/cli.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/pipeline/cli.py): CLI commands `process-text`, `nlp-stats`, `nlp-validate`, and `resolve-entity`.

---

### 3. Test Verification & Benchmark Results
- 18 new comprehensive unit and integration tests in [`tests/test_nlp.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/tests/test_nlp.py).
- **All 53 project tests passed in 5.24s**:
  ```text
  tests/test_commentary_adapter.py: 2 passed
  tests/test_cricsheet_adapter.py: 2 passed
  tests/test_integration.py: 1 passed
  tests/test_news_adapter.py: 1 passed
  tests/test_nlp.py: 18 passed
  tests/test_pipeline.py: 20 passed
  tests/test_schemas.py: 5 passed
  tests/test_storage.py: 4 passed
  ======================= 53 passed, 3 warnings in 5.24s ========================
  ```
- **Fixture Evaluation Benchmark Metrics**:
  - NER Precision / Recall / F1: **1.000 / 1.000 / 1.000** (Zero false positives, exact character spans verified).
  - Unambiguous Entity Resolution: **100.0%** ($\ge 0.95$ confidence).
  - Ambiguity Preservation: **100.0%** (isolated ambiguous surnames score 0.40, remaining `UNRESOLVED`).
  - Contextual Disambiguation: **100.0%** (team context adds +0.35 boost $\to 0.75$, resolving accurately).
  - Sentiment Macro-F1 on Fixtures: **1.00** (Negation inversion and bowler/batter framing verified).

---

### 4. Documentation Deliverables Created / Updated
- [`docs/NLP_PIPELINE.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/NLP_PIPELINE.md): Pipeline architecture, normalizer, tokenizer, NER, resolver, and CLI.
- [`docs/CRICKET_ENTITY_RESOLUTION.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/CRICKET_ENTITY_RESOLUTION.md): Multi-signal ranking, team context cues, and ambiguity margins.
- [`docs/SENTIMENT_BASELINES.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SENTIMENT_BASELINES.md): Sentiment baselines, negation window, event polarity vs entity framing.
- [`docs/NLP_EVALUATION.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/NLP_EVALUATION.md): Quantitative benchmark metrics and fixture results.
- [`docs/DATA_MODEL.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/DATA_MODEL.md): Updated with Schema Version 3 NLP tables.
- [`docs/ARCHITECTURE.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/ARCHITECTURE.md): Updated Modules F and G.
- [`docs/SECURITY_AND_LICENSING.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SECURITY_AND_LICENSING.md): Updated with Section 6 (NLP Licensing & Privacy Safeguards).

---

### 5. Next Checkpoint & Action
Proceed to **Phase 5: Semantic Embeddings, Topic Discovery, Alignment & Attention Analytics**.

---

## Session 06: Phase 5 Plan — Semantic Embeddings, Topic Discovery & Narrative Intelligence
- **Date**: 2026-10-20
- **Lead Role**: Senior NLP/ML Researcher & Data Architect
- **Current Phase**: Phase 5 (Semantic Embeddings & Narrative Intelligence)
- **Status**: COMPLETED

---

### 1. Phase 5 Objectives Achieved
1. Implemented a modular, reproducible, CPU-first analysis package under `src/analysis/` for semantic embeddings, topic clustering, and narrative alignment.
2. Built a model-agnostic embedding interface with an explicit, deterministic test double (`DeterministicTestEmbeddingModel`) yielding normalized 384-dimensional vectors, and documented opt-in support for `sentence-transformers/all-MiniLM-L6-v2`.
3. Implemented an interpretable sparse TF-IDF baseline preserving cricket syntax (`19.4`, `182/5`, `82*`, `DRS`).
4. Built modular topic clustering (`TopicClusterer`) supporting K-Means and DBSCAN with class-based TF-IDF (`TopicLabeler`) keyword extraction and outlier tagging (`-1` as `"Outliers / Noise"`).
5. Implemented clustering quality evaluation (`evaluate_topic_clustering`) computing silhouette score, Davies-Bouldin index, cluster size distributions, noise fractions, and intra/inter-cluster similarities.
6. Built conservative two-stage cross-source retrieval and ranking (`CrossSourceNarrativeMatcher`) between editorial paragraphs, commentary deliveries, and structured match facts.
7. Constructed structured narrative timelines (`NarrativeTimelineEngine`) distinguishing observed from inferred timestamps.
8. Upgraded SQLite to Schema Version 4 (`embedding_records`, `topic_runs`, `topic_clusters`, `topic_assignments`, `cross_source_matches`, `timeline_snapshots`) with vector array caching.
9. Integrated Phase 5 CLI commands (`embed-text`, `cluster-topics`, `evaluate-topics`, `narrative-timeline`, `analysis-stats`, `analysis-validate`).
10. Added 18 new unit and integration tests in `tests/test_analysis.py`, bringing the total project test suite to 71 passing tests.

---

### 2. Modules Created & Extended

- [`src/analysis/analysis_schemas.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/analysis/analysis_schemas.py): Pydantic v2 schemas for embeddings, topic runs, clusters, assignments, cross-source matches, and narrative timeline points.
- [`src/analysis/embedding_models.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/analysis/embedding_models.py): `BaseEmbeddingModel`, `DeterministicTestEmbeddingModel` (test double), and lazy-loaded `SentenceTransformerEmbeddingModel`.
- [`src/analysis/similarity.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/analysis/similarity.py): Cosine similarity, batch similarity matrices, and top-$K$ candidate retrieval.
- [`src/analysis/tfidf_baseline.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/analysis/tfidf_baseline.py): `CricketTfidfBaseline` with cricket-preserving token patterns.
- [`src/analysis/topic_clustering.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/analysis/topic_clustering.py): `TopicClusterer` with K-Means and DBSCAN noise handling.
- [`src/analysis/topic_labeling.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/analysis/topic_labeling.py): `TopicLabeler` with c-TF-IDF keyword extraction and representative document selection.
- [`src/analysis/topic_evaluation.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/analysis/topic_evaluation.py): `evaluate_topic_clustering` computing geometric and distribution metrics.
- [`src/analysis/narrative_similarity.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/analysis/narrative_similarity.py): `CrossSourceNarrativeMatcher` two-stage retrieval and ranking engine.
- [`src/analysis/event_alignment.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/analysis/event_alignment.py): `EventAlignmentEngine` synthesizing milestones (wickets, powerplays, death overs) and computing paragraph alignments.
- [`src/analysis/narrative_timeline.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/analysis/narrative_timeline.py): `NarrativeTimelineEngine` temporal trajectory tracking.
- [`src/analysis/embedding_pipeline.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/analysis/embedding_pipeline.py): Batch embedding generation with SHA-256 caching and vector persistence.
- [`src/storage/sqlite_manager.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/storage/sqlite_manager.py): Upgraded to `SCHEMA_VERSION = 4` with DDL and upsert methods.
- [`src/pipeline/cli.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/pipeline/cli.py): CLI commands `embed-text`, `cluster-topics`, `evaluate-topics`, `narrative-timeline`, `analysis-stats`, `analysis-validate`.
- [`tests/test_analysis.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/tests/test_analysis.py): 18 comprehensive tests.

---

### 3. Test Verification & Suite Results
- **All 71 project tests passed in 9.31s** across all 9 test modules:
  ```text
  tests/test_analysis.py: 18 passed
  tests/test_commentary_adapter.py: 2 passed
  tests/test_cricsheet_adapter.py: 2 passed
  tests/test_integration.py: 1 passed
  tests/test_news_adapter.py: 1 passed
  tests/test_nlp.py: 18 passed
  tests/test_pipeline.py: 20 passed
  tests/test_schemas.py: 5 passed
  tests/test_storage.py: 4 passed
  ======================= 71 passed, 3 warnings in 9.31s ========================
  ```

---

### 4. Documentation Deliverables Created / Updated
- [`docs/EMBEDDINGS.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/EMBEDDINGS.md): Architecture, model governance, test doubles, and caching protocol.
- [`docs/TOPIC_DISCOVERY.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/TOPIC_DISCOVERY.md): TF-IDF vs dense embeddings, K-Means, DBSCAN, and c-TF-IDF.
- [`docs/NARRATIVE_ANALYSIS.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/NARRATIVE_ANALYSIS.md): Two-stage cross-source matching, milestone synthesis, and timeline tracking.
- [`docs/ANALYSIS_EVALUATION.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/ANALYSIS_EVALUATION.md): Benchmarks, metrics, and storage invariants.
- [`docs/DATA_MODEL.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/DATA_MODEL.md): Updated with Schema Version 4 tables.
- [`docs/ARCHITECTURE.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/ARCHITECTURE.md): Updated Modules H, I, and J.
- [`docs/SECURITY_AND_LICENSING.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SECURITY_AND_LICENSING.md): Updated with Section 7 (Semantic Embeddings & Analysis Safeguards).

---

### 5. Next Checkpoint & Action
Proceed to **Phase 6: Media Attention vs Performance Analytics, Serving API & Dashboard Presentation**.

---

## Session 07 — 2026-10-20 (Phase 6A: Media Attention vs Performance Analytics Engine)

### 1. Objectives & Scope
- Build an evidence-driven analytical engine that measures how media attention and narrative framing compare with actual player, team, and match performance.
- Compute the Attention-to-Performance Discrepancy Index (APDI): $\text{APDI} = \text{NormAttention} - \text{NormPerformance}$ within role cohorts.
- Separate attention volume, reach, publisher diversity, and prominence from objective cricket performance metrics (runs, SR, wickets, economy, match phases).
- Implement strict data quality gates (`INSUFFICIENT_DATA` handling) and auditable lineage/evidence tracking.
- Analytical engine and CLI only (Serving API and Frontend deferred to subsequent subphases).

### 2. Implementation Plan & Completed Execution
- **Schema & Persistence**: Upgraded to SQLite Schema Version 5 (`attention_metrics`, `performance_metrics`, `apdi_records`, `analytics_runs`).
- **Analytics Engine**:
  - `src/analytics/schemas.py`: Canonical analytics models (`MediaAttentionMetrics`, `CricketPerformanceMetrics`, `NarrativeFramingMetrics`, `APDIRecord`, `PreflightCheckResult`, `AnalyticsRunRecord`).
  - `src/analytics/attention.py`: `MediaAttentionCalculator` computing paragraph volume, raw mentions, corpus reach, source diversity, prominence scoring (headline/lead/body), and event-linked mentions.
  - `src/analytics/performance.py`: `CricketPerformanceCalculator` enforcing ICC cricket scoring semantics (extras, legal deliveries, byes/leg-byes exclusion from bowler runs, bowler-credited wickets) and role composites.
  - `src/analytics/framing.py`: `NarrativeFramingCalculator` computing entity-targeted sentiment distributions, net framing scores, publisher breakdowns, and supporting text snippets.
  - `src/analytics/apdi.py`: `APDICalculator` computing percentile-normalized attention and performance within role cohorts, APDI discrepancy index, and strict `INSUFFICIENT_DATA` gates.
  - `src/analytics/preflight.py`: `AnalyticsPreflight` validating match scorecard reconciliation, canonical entities, and corpus sufficiency.
  - `src/analytics/__init__.py`: Clean exports.
- **CLI Subcommands** (`src/pipeline/cli.py`):
  - `analytics-preflight`: Quality gate audit and eligibility check.
  - `compute-attention`: Editorial attention extraction and prominence calculation.
  - `compute-performance`: Objective batting, bowling, and team performance metrics.
  - `compute-apdi`: Discrepancy index evaluation across cohorts.
  - `analytics-report`: Summary leaderboard and deep evidence lineage inspection.
  - `analytics-validate`: Structural invariant verification across all Phase 6A tables.
- **Testing & Verification**:
  - `tests/test_analytics.py`: 9 comprehensive test suites covering cricket invariants, attention, framing, APDI classifications (`OVER_ATTENDED`, `UNDER_ATTENDED`, `BALANCED`, `INSUFFICIENT_DATA`), and storage v5 CRUD.
  - Full project test suite: **80 tests passed in 10.68s**.
- **Documentation Deliverables**:
  - `docs/MEDIA_ATTENTION_METRICS.md`
  - `docs/PERFORMANCE_METRICS.md`
  - `docs/APDI_METHODOLOGY.md`
  - `docs/ANALYTICS_EVALUATION.md`
  - `docs/DATA_MODEL.md` (Updated with Schema Version 5)
  - `docs/ARCHITECTURE.md` (Updated with Module K: Attention vs Performance Analytics)

### 3. Verification & Live Corpus Status
- **Empty Database Truthfulness**: Verified that database currently records 0 matches, 0 deliveries, 0 articles, and 0 normalized texts.
- **Preflight & APDI**: Correctly reports `INSUFFICIENT_DATA` rather than hallucinating speculative findings.
- **Invariant Validation**: `python -m src.pipeline analytics-validate` passes with 0 issues.

### 4. Next Checkpoint & Action
Proceed to **Phase 6B: FastAPI Serving Layer & Analytics Endpoints**.

---

## Session 08 — 2026-10-24 (Phase 6B: FastAPI Serving Layer & Research API)

### 2. Implementation & Components Created
- **API Package Structure (`src/api/`)**:
  - `src/api/config.py`: Environment-backed `APISettings` managing database paths, CORS whitelist, pagination limits, and OpenAPI metadata.
  - `src/api/dependencies.py`: Dependency injection providers for `SQLiteStorageManager`, `AnalyticsPreflight`, analytics calculators, and pagination bounds.
  - `src/api/errors.py`: Custom API exception hierarchy (`ResourceNotFoundError`, `InvalidParameterError`, `DatabaseError`) and centralized exception handlers rendering uniform `ErrorResponse` envelopes without leaking database details.
  - `src/api/schemas/`: Explicit Pydantic response models (`common.py`, `matches.py`, `entities.py`, `editorial.py`, `nlp.py`, `analytics.py`, `observability.py`).
  - `src/api/routes/`: Route modules covering all 7 required functional areas (`health.py`, `matches.py`, `players.py`, `teams.py`, `articles.py`, `commentary.py`, `nlp.py`, `analytics.py`, `observability.py`).
  - `src/api/main.py`: Application factory `create_app()` with async lifespan persistence initialization, restrictive CORS middleware, and automatic OpenAPI documentation.
- **Testing Suite (`tests/test_api.py`)**:
  - 16 comprehensive integration and unit tests covering application startup, liveness, readiness, empty-state collections, 404 handling, pagination boundaries, SQL injection resistance, populated match performance calculations, canonical entities, article/commentary retrieval, topic clusters, narrative timeline, APDI status preservation, analytics validation, observability without credential leakage, and CORS preflight.
  - All tests execute against temporary, isolated SQLite databases. Real databases are never mutated.

### 3. Test Verification & Suite Results
- **Full Test Suite Results**: **96 passed, 0 failed in 97.53s**:
  ```text
  tests/test_analysis.py: 18 passed
  tests/test_analytics.py: 9 passed
  tests/test_api.py: 16 passed
  tests/test_commentary_adapter.py: 2 passed
  tests/test_cricsheet_adapter.py: 2 passed
  tests/test_integration.py: 1 passed
  tests/test_news_adapter.py: 1 passed
  tests/test_nlp.py: 18 passed
  tests/test_pipeline.py: 20 passed
  tests/test_schemas.py: 5 passed
  tests/test_storage.py: 4 passed
  ================== 96 passed, 6 warnings in 97.53s ==================
  ```
- **Live Smoke Test Outcome**:
  - `/health`: HTTP 200 `{'status': 'healthy', 'version': '1.0.0'}`
  - `/ready`: HTTP 200 `{'status': 'ready', 'database_accessible': True, 'schema_version': 5, 'database_tables_count': 28}`
  - `/api/v1/status`: HTTP 200 `{'pipeline_status': 'empty', 'data_sufficiency_status': 'INSUFFICIENT_DATA', 'is_analytics_ready': False}`
  - `/api/v1/matches`: HTTP 200 `{'items': [], 'pagination': {'total': 0, 'limit': 20, 'offset': 0, 'has_more': False}}`
  - `/openapi.json`: HTTP 200 with 32 documented endpoint paths.

### 4. Documentation Deliverables
- [`docs/API_DOCUMENTATION.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/API_DOCUMENTATION.md): Complete REST endpoint reference, query parameters, schemas, error codes, and local startup instructions.
- [`src/api/README.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/api/README.md): Quick developer guide for the API package.
- [`docs/ARCHITECTURE.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/ARCHITECTURE.md): Updated Module L with API architectural patterns.

### 5. Next Checkpoint & Action
Phase 6B is verified and complete. Proceed to **Phase 6C: Frontend & Intelligence Dashboard** when ready.

---

## Session 09 — 2026-10-24 (Phase 6C: T20 Cricket Intelligence Dashboard)

### 1. Objectives & Scope
- Build Phase 6C: a polished, responsive React dashboard for exploring cricket matches, player performance, media coverage, editorial narratives, topic clusters, cross-source event alignments, source provenance, and the Attention-to-Performance Discrepancy Index (APDI).
- Strictly adhere to data truthfulness: no synthetic scores, fabricated players, or artificial results.
- Honor existing Phase 6A methodology: preserve `INSUFFICIENT_DATA` and display `null` scores as `unavailable`, never coerced to zero.
- Connect to actual FastAPI backend running at `http://127.0.0.1:8000`.
- Frontend implementation only (located in `frontend/`). No modifications to historical analytics math or backend endpoints.

### 2. Implementation & Components Created

1. **Frontend Infrastructure & Tooling (`frontend/`)**:
   - `package.json`: Configured with React 18, TypeScript 5 (Strict Mode), Vite 6, Tailwind CSS 3, Lucide React, Recharts, React Router DOM 6, TanStack React Query 5, Axios, Vitest, Testing Library.
   - `tsconfig.json` & `vite.config.ts`: Strict TypeScript compiler options with `@/*` aliases and dev server proxy routing `/api`, `/health`, `/ready` to `127.0.0.1:8000`.
   - `tailwind.config.js` & `src/index.css`: Cricket pitch emerald (`#10b981`), crimson wicket (`#e11d48`), boundary gold (`#f59e0b`), dark navy foundation (`#020617` / `#0b1329`), and customized typography.

2. **Types & Centralized API Client (`frontend/src/`)**:
   - `src/types/api.ts`: Comprehensive TypeScript interfaces strictly mirroring all 32 endpoints, canonical Pydantic models, and pagination envelopes from the FastAPI backend.
   - `src/lib/api.ts`: Centralized, typed Axios client with safe error extractor (`extractErrorMessage`), request timeouts (15s), and query functions for all 7 functional areas.
   - `src/context/ThemeContext.tsx`: Theme provider with dark/light mode toggle and persistent state.

3. **Reusable Design System (`frontend/src/components/`)**:
   - `ui/`: `Card`, `Badge` (with APDI category variants `over_attended`, `under_attended`, `balanced`, `insufficient_data`), `Button`, `MetricCard`, `EmptyState` (with CLI remediation commands), `ErrorState` (with retry button), `Skeleton`, `Table`.
   - `layout/`: `Sidebar` (responsive collapsible sidebar with all 8 navigation items), `Header` (live backend probe, tournament scope selector, theme toggle), `AppLayout`.

4. **Required Feature Modules (`frontend/src/features/`)**:
   - `overview/OverviewPage.tsx`: Primary research dashboard with quality gate status, corpus data coverage metrics, APDI distribution snapshot, and unpopulated corpus notice.
   - `matches/MatchesPage.tsx`: Paginated tournament match directory with tournament/season filters, delivery-derived scorecard drawer, batting strike rates, and bowling economies.
   - `players/PlayersPage.tsx`: Player directory with search by name/alias, role badges, objective metrics (batting average, bowling SR), and associated media prominence.
   - `media/MediaPage.tsx`: Dual-tab explorer for news journalism articles and ball-by-ball commentary, source domain filtering, paragraph segment inspector, and publisher framing distributions.
   - `narratives/NarrativesPage.tsx`: Topic clusters with c-TF-IDF keywords, entity mentions with resolution tags (`RESOLVED`, `AMBIGUOUS`, `UNRESOLVED`), narrative timeline, and cross-source match alignments.
   - `apdi/APDIPage.tsx`: Core APDI explorer featuring mathematical formulation reference, cohort percentile distribution, discrepancy badges, evidence lineage audit, and strict preservation of `null` scores.
   - `sources/SourcesPage.tsx`: Provenance records, crawler pipeline stats, ingestion runs, and analytics batch history.
   - `health/HealthPage.tsx`: Independent four-tier diagnostic probes (Process Liveness, SQLite Persistence, Data Availability, and Analytics Quality Gate) with structural validation audit.

### 3. Test Verification & Quality Gates

1. **Frontend Vitest Suite (`npm run test`)**:
   - `src/test/api.test.ts` (4 tests): Client configuration, endpoint formatting, error extraction.
   - `src/test/app.test.tsx` (1 test): Application shell, routing, navigation.
   - `src/test/features.test.tsx` (4 tests): APDI `INSUFFICIENT_DATA` null preservation, Matches empty states, Health 4-tier diagnostic verification, Overview unpopulated notice.
   - **Result**: **3 test files, 9 tests passed in 17.79s**.

2. **TypeScript Compilation (`npm run typecheck`)**:
   - `tsc --noEmit` executed with 0 errors.

3. **Vite Production Build (`npm run build`)**:
   - `vite build` completed cleanly in 51.70s with production bundle emitted to `frontend/dist/`.

4. **Python Regression Suite (`pytest tests/`)**:
   - Ran `python -m pytest tests/` from repository root: **96 passed, 0 failed in 68.99s**.

### 4. Git & Repository Status
- Added frontend files to repository.
- Updated `.gitignore` to explicitly ignore `frontend/node_modules/`, `frontend/dist/`, `.vite/`.
- Updated `docs/ARCHITECTURE.md` with Module L Frontend Research Dashboard.
- Created `frontend/README.md`.



