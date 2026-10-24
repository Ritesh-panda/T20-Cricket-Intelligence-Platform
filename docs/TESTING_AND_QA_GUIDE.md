# T20 Cricket Intelligence Platform — Complete Testing & QA Guide

**Document Version**: 2.0.0  
**Target Release**: Production Ready (Post-Phase 9 Release)  
**Primary Audience**: Software Development Engineers in Test (SDET), QA Engineers, Core Contributors, and Independent Auditors  

---

## 1. Testing Philosophy & Test Infrastructure

The testing architecture of the **T20 Cricket Intelligence Platform** enforces strict scientific validity, deterministic reproducibility, and failure isolation.

### 1.1 Test Engineering Standards
1. **Deterministic Execution**: Zero flaky tests. Random seeds (`random_state=42`) and deterministic hash mocks guarantee identical outcomes across all operating systems.
2. **Isolation from Production State**: Unit and integration test suites run against **temporary in-memory or isolated SQLite databases** (`tmp_path`). Never mutate `data/cricket_intel.db` during routine test runs.
3. **No External Network Dependencies**: Tests must execute 100% offline. No live HTTP calls to Wikipedia, Cricsheet, or commercial APIs are permitted in unit tests.
4. **Strict Null Preservation**: Assert that missing values (`apdi_value = NULL`, unknown publication dates, unsupported match links) remain explicitly `None`/`null` without fallback fabrication.
5. **Scorecard Ground-Truth Invariance**: Any scorecard calculation must match raw ball-by-ball facts to the single ball and run.

### 1.2 Test Execution Commands

```bash
# 1. Run Complete Python Test Suite (112 tests)
python -m pytest tests/ -v

# 2. Run Specific Subsystem Tests
python -m pytest tests/test_storage.py -v          # Storage & database transactions
python -m pytest tests/test_nlp.py -v              # NER, entity resolution & sentiment
python -m pytest tests/test_analytics.py -v        # Performance, attention & APDI
python -m pytest tests/test_api.py -v              # FastAPI routes and schemas
python -m pytest tests/test_phase8_regression.py -v # Phase 8 regression tests
python -m pytest tests/test_phase9_validity.py -v   # Phase 9 validity & provenance tests

# 3. Run Frontend Vitest Suite (9 tests)
cd frontend
npm run test

# 4. Run TypeScript Typecheck
npm run typecheck

# 5. Run Frontend Production Bundle Build
npm run build

# 6. Execute Deterministic Ground-Truth Validation Scripts
python scripts/phase8_inventory_audit.py
python scripts/validate_raw_matches_against_db.py
python scripts/phase9_apdi_sensitivity.py
python scripts/evaluate_nlp_gold_set.py
```

---

## 2. Exhaustive Function-by-Function Testing Reference

---

### Subsystem 1: Source Adapters & Ingestion (`src/adapters/`)

#### 1.1 `CricsheetAdapter.parse_match_json(raw_data: Dict[str, Any], source_identifier: str)`
- **Module**: `src.adapters.cricsheet_adapter`
- **Signature**: `(raw_data: Dict[str, Any], source_identifier: str) -> Tuple[MatchRecord, List[DeliveryRecord], SourceRecord]`
- **Functional Purpose**: Parses official Cricsheet JSON (v1.2.0) into canonical `MatchRecord`, delivery sequences, and immutable `SourceRecord`.
- **Target Invariants**:
  - Every ball must be attributed to an inning (1, 2, or Super Over 3/4).
  - Extras (`wides`, `noballs`, `byes`, `legbyes`) must be segregated from batter runs.
  - Legal ball flag (`is_legal`) must be `0` for wides and no-balls, `1` otherwise.
  - Phase must be classified deterministically: Overs 0–5 (`POWERPLAY`), 6–15 (`MIDDLE`), 16–19 (`DEATH`).
- **Edge Cases to Test**:
  - Super Overs (Match `1415711`: 270 total balls, 4 innings).
  - DLS rain-revised matches (Match `1415744`: 10/11 overs shortened).
  - Abandoned matches with zero deliveries (Match `1415750`).
  - Penalty runs and retired hurt dismissals.
- **How to Test**:
  - Test: `tests/test_cricsheet_adapter.py::test_parse_cricsheet_match`
  - Command: `pytest tests/test_cricsheet_adapter.py -k test_parse`

#### 1.2 `NewsArticleAdapter.parse_html(html_content: str | bytes, canonical_url: str, source_domain: Optional[str])`
- **Module**: `src.adapters.news_adapter`
- **Signature**: `(html_content: str | bytes, canonical_url: str, source_domain: Optional[str] = None) -> Tuple[ArticleRecord, List[ArticleParagraphRecord], SourceRecord]`
- **Functional Purpose**: Extracts body text, headline, byline, and publication date using Trafilatura with BeautifulSoup fallback. Segments body into discrete paragraph records.
- **Target Invariants**:
  - Content hash must be 64-character SHA-256 hex string.
  - If `<time>` datetime is absent, `published_at_utc` must be `None` (never set to current time).
  - Paragraphs with $< 25$ characters (disclaimers/nav noise) must be filtered out.
  - Paragraph IDs must follow format `{article_id}_p{index}`.
- **Edge Cases to Test**:
  - HTML with missing `<title>` or OpenGraph tags (fallback to `<h1>` or default).
  - Malformed HTML with non-closing tags.
  - Short boilerplate articles ($< 50$ words) raising `ValueError`.
  - Content with multiple ISO 8601 date formats (`Z` vs `+00:00`).
- **How to Test**:
  - Test: `tests/test_news_adapter.py::test_parse_sample_news_article`
  - Test: `tests/test_phase9_validity.py::test_null_publication_date_preservation`

#### 1.3 `CommentaryAdapter.parse_commentary_stream(raw_text: str, match_id: str)`
- **Module**: `src.adapters.commentary_adapter`
- **Signature**: `(raw_text: str, match_id: str) -> Tuple[List[CommentaryRecord], SourceRecord]`
- **Functional Purpose**: Parses ball-by-ball text feeds, extracting over, ball, bowler, batter, text, and event excitement keywords.
- **Target Invariants**:
  - Regex must extract standard formats (e.g., `19.4 Bumrah to Klaasen, FOUR`).
  - Over and ball numbers must be non-negative integers.
- **How to Test**:
  - Test: `tests/test_commentary_adapter.py::test_parse_valid_commentary_stream`

---

### Subsystem 2: Storage & Persistence Engine (`src/storage/sqlite_manager.py`)

#### 2.1 `SQLiteStorageManager.__init__(db_path: str | Path)`
- **Signature**: `(db_path: str | Path) -> None`
- **Functional Purpose**: Connects to SQLite database, enables WAL mode (`PRAGMA journal_mode = WAL`), turns on foreign keys (`PRAGMA foreign_keys = ON`), and applies DDL schema migrations up to version 5.
- **Invariants**: Schema migrations table must record version `5`.

#### 2.2 `SQLiteStorageManager.record_provenance(record: SourceRecord) -> bool`
- **Signature**: `(record: SourceRecord) -> bool`
- **Functional Purpose**: Inserts an immutable provenance audit record into `source_records`.
- **Invariants**: Returns `True` on insert, `False` on duplicate content hash (`ON CONFLICT(content_hash_sha256) DO NOTHING`).

#### 2.3 `SQLiteStorageManager.insert_deliveries_batch(deliveries: List[DeliveryRecord]) -> int`
- **Signature**: `(deliveries: List[DeliveryRecord]) -> int`
- **Functional Purpose**: Atomically inserts thousands of deliveries inside a single SQLite transaction using `executemany`.
- **Edge Cases to Test**:
  - Empty deliveries list returns `0`.
  - Foreign key violation if `match_id` does not exist in `matches`.
- **How to Test**:
  - Test: `tests/test_storage.py::test_batch_delivery_insertion`

#### 2.4 `SQLiteStorageManager.insert_article_with_paragraphs(article: ArticleRecord, paragraphs: List[ArticleParagraphRecord]) -> Tuple[bool, str]`
- **Signature**: `(article: ArticleRecord, paragraphs: List[ArticleParagraphRecord]) -> Tuple[bool, str]`
- **Functional Purpose**: Inserts article and its paragraph segments within a single transaction with strict deduplication.
- **Target Invariants**:
  - Queries `SELECT article_id FROM articles WHERE canonical_url = ? OR raw_content_hash = ?`.
  - If match exists, aborts transaction and returns `(False, "Duplicate detected: ...")`.
  - If new, inserts article and all paragraphs, returning `(True, article_id)`.
- **How to Test**:
  - Test: `tests/test_phase9_validity.py::test_duplicate_ingestion_idempotence`

#### 2.5 `SQLiteStorageManager.upsert_apdi_records(records: List[APDIRecord]) -> int`
- **Signature**: `(records: List[APDIRecord]) -> int`
- **Functional Purpose**: Upserts APDI records, using `ON CONFLICT(record_id) DO UPDATE` to overwrite previous evaluations for the same entity run while preserving historical `run_id` audit traces.
- **Invariants**: `apdi_value` must be saved as `NULL` when `record.apdi_value is None`.

#### 2.6 `SQLiteStorageManager.get_analytics_summary(tournament: Optional[str]) -> Dict[str, Any]`
- **Signature**: `(tournament: Optional[str] = None) -> Dict[str, Any]`
- **Functional Purpose**: Aggregates metric counts across `attention_metrics`, `performance_metrics`, and `apdi_records`.
- **Target Invariants**:
  - Includes tournament alias resolution (matching `"ICC Men's T20 World Cup"` when queried with `"T20 World Cup 2024"`).
  - Returns exact keys: `tournament`, `attention_metrics_count`, `performance_metrics_count`, `apdi_records_count`, `over_attended_count`, `under_attended_count`, `balanced_count`, `insufficient_data_count`, `analytics_runs_count`.
- **How to Test**:
  - Test: `tests/test_phase8_regression.py::test_storage_analytics_summary_alias`
  - Test: `tests/test_phase9_validity.py::test_database_and_api_inventory_consistency`

---

### Subsystem 3: Natural Language Processing (`src/nlp/`)

#### 3.1 `CricketNER.extract_mentions(text: str, source_type: str, source_id: str) -> List[EntityMentionRecord]`
- **Module**: `src.nlp.ner`
- **Signature**: `(text: str, source_type: str = "editorial", source_id: str = "") -> List[EntityMentionRecord]`
- **Functional Purpose**: Scans input text for cricket entity mentions (players, teams, venues) using trie gazetteer lookups, regex patterns, and title-case noun chunk extraction.
- **Target Invariants**:
  - Returns `EntityMentionRecord` with character start/end spans (`start_char`, `end_char`).
  - Text slice `text[start_char:end_char]` must exactly equal `surface_text`.
- **How to Test**:
  - Test: `tests/test_nlp.py::test_ner_extraction_spans`

#### 3.2 `EntityResolver.resolve_mentions(mentions: List[EntityMentionRecord], doc_text: str) -> Tuple[List[EntityMentionRecord], List[DisambiguationRecord]]`
- **Module**: `src.nlp.entity_resolver`
- **Signature**: `(mentions: List[EntityMentionRecord], doc_text: str = "") -> Tuple[List[EntityMentionRecord], List[DisambiguationRecord]]`
- **Functional Purpose**: Maps raw surface text (e.g., "Kohli", "Rohit", "Men in Blue") to canonical entity IDs (`player_virat_kohli`, `team_ind`).
- **Disambiguation Rules**:
  - Unambiguous full name: Resolves with `confidence = 0.95`.
  - Common surname without initials (e.g., "Sharma"): Checks document-level team co-occurrence. If co-occurring team is India, resolves to `player_rohit_sharma`; if ambiguous, marks `AMBIGUOUS`.
  - Unregistered name: Marks `UNRESOLVED` with `resolved_id = None`.
- **How to Test**:
  - Test: `tests/test_nlp.py::test_entity_resolution_rules`
  - Script: `python scripts/evaluate_nlp_gold_set.py` (Must yield 80.0% accuracy, 0% false associations).

#### 3.3 `CricketSentimentAnalyzer.analyze_sentence(sentence: str, target_entity: str) -> SentimentBaselineRecord`
- **Module**: `src.nlp.sentiment`
- **Signature**: `(sentence: str, target_entity: str) -> SentimentBaselineRecord`
- **Functional Purpose**: Evaluates sentiment polarity with cricket-specific lexicon overrides (e.g., "duck", "collapse", "choke" = negative; "blitz", "hat-trick", "clinical" = positive).
- **Target Invariants**:
  - Polarity compound score strictly bounded in $[-1.0, +1.0]$.
  - Sentiment label classified as `POSITIVE` ($> 0.05$), `NEGATIVE` ($< -0.05$), or `NEUTRAL`.
- **How to Test**:
  - Test: `tests/test_nlp.py::test_cricket_lexicon_sentiment`

---

### Subsystem 4: Semantic Analysis & Topic Modeling (`src/analysis/`)

#### 4.1 `EmbeddingPipeline.run_pipeline(texts: List[str], document_ids: List[str]) -> EmbeddingRunResult`
- **Module**: `src.analysis.embedding_pipeline`
- **Signature**: `(texts: List[str], document_ids: List[str]) -> EmbeddingRunResult`
- **Functional Purpose**: Encodes text paragraphs into 384-dimensional dense vectors using `sentence-transformers/all-MiniLM-L6-v2`.
- **Target Invariants**:
  - Output numpy array shape must be `(len(texts), 384)`.
  - Vectors must be strictly L2-normalized: `np.linalg.norm(vec) == 1.0000 ± 1e-5`.
  - Cache persistence must store `vectors_{model_slug}.npy`.
- **How to Test**:
  - Test: `tests/test_analysis.py::test_embedding_vector_dimensions_and_norm`

#### 4.2 `TopicClusterer.fit_predict(matrix: np.ndarray) -> np.ndarray`
- **Module**: `src.analysis.topic_clustering`
- **Signature**: `(matrix: np.ndarray) -> np.ndarray`
- **Functional Purpose**: Unsupervised K-Means clustering ($k=3$, `random_state=42`, `n_init=10`).
- **Target Invariants**:
  - Cluster labels must be integers in range `[0, k-1]`.
  - Cluster centers array shape must be `(k, 384)`.
- **How to Test**:
  - Test: `tests/test_analysis.py::test_topic_clustering_reproducibility`

#### 4.3 `EventAlignmentEngine.align_editorial_to_milestones(...)`
- **Module**: `src.analysis.event_alignment`
- **Functional Purpose**: Assesses evidence-backed links between paragraphs and match events.
- **Invariants**: When commentary is absent, must produce 0 false alignments and report `NOT_EVALUABLE`.

---

### Subsystem 5: Analytics & APDI Engine (`src/analytics/`)

#### 5.1 `StructuredPerformanceEngine.calculate_batting_metrics(deliveries, batter_id)`
- **Module**: `src.analytics.performance`
- **Functional Purpose**: Standardizes batting performance from deliveries.
- **Formulas**:
  - $\text{StrikeRate} = (\text{Runs} / \text{BallsFaced}) \times 100$
  - $\text{BoundaryPct} = (\text{RunsFromFoursAndSixes} / \text{Runs}) \times 100$
  - $\text{Composite} = 0.35 \cdot \text{NormRuns} + 0.35 \cdot \text{NormSR} + 0.30 \cdot \text{NormBoundaryPct}$
- **Edge Cases**: Batter with 0 balls faced returns strike rate `None`, composite `0.0`.

#### 5.2 `StructuredPerformanceEngine.calculate_bowling_metrics(deliveries, bowler_id)`
- **Module**: `src.analytics.performance`
- **Formulas**:
  - $\text{EconomyRate} = \text{RunsConceded} / (\text{LegalBalls} / 6.0)$
  - $\text{DotBallPct} = (\text{DotBalls} / \text{LegalBalls}) \times 100$
  - $\text{Composite} = 0.40 \cdot \text{NormWickets} + 0.35 \cdot (1 - \text{NormEconomy}) + 0.25 \cdot \text{NormDotPct}$

#### 5.3 `MediaAttentionEngine.calculate_entity_attention(...)`
- **Module**: `src.analytics.attention`
- **Formulas**:
  - $\text{ProminenceScore} = 1.0 \cdot \text{BodyMentions} + 2.0 \cdot \text{LeadMentions} + 3.0 \cdot \text{HeadlineMentions}$
  - Tracks article reach, paragraph count, and source diversity.

#### 5.4 `APDICalculator.compute_cohort_apdi(role, entities_data, run_id, tournament, comparison_window)`
- **Module**: `src.analytics.apdi`
- **Signature**: `(role: CohortRole, entities_data: List[Tuple], run_id: Optional[str] = None, tournament: str = ..., comparison_window: str = ...) -> List[APDIRecord]`
- **Functional Purpose**: Computes cohort percentile ranks and discrepancy index.
- **Target Invariants**:
  - Batters, bowlers, and teams are normalized strictly within their own cohort.
  - Entities failing minimum criteria (balls faced $< 10$, balls bowled $< 12$, mentions $< 1$) receive:
    - `apdi_value = None`
    - `discrepancy_category = INSUFFICIENT_DATA`
    - `evidence_sufficiency_status = INSUFFICIENT_DATA`
  - Valid entities receive:
    - $\text{APDI} = \text{NormAttention} - \text{NormPerformance} \in [-1.0, +1.0]$
    - Category: `OVER_ATTENDED` ($> 0.20$), `UNDER_ATTENDED` ($< -0.20$), `BALANCED` (otherwise).
- **How to Test**:
  - Test: `tests/test_analytics.py::test_apdi_calculation_logic`
  - Test: `tests/test_phase9_validity.py::test_null_apdi_propagation_for_insufficient_data`
  - Test: `tests/test_phase9_validity.py::test_cross_cohort_percentile_isolation`

#### 5.5 `AnalyticsPreflight.check(tournament: Optional[str]) -> PreflightCheckResult`
- **Module**: `src.analytics.preflight`
- **Functional Purpose**: Audits active database prior to analytical computation.
- **Invariants**: Must resolve tournament aliases and verify that match deliveries $> 0$.

---

### Subsystem 6: FastAPI REST API Routes (`src/api/routes/`)

| Method | Path | Target Parameters | Expected Status | Invariants / Edge Cases to Test |
| :--- | :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/status` | None | `200 OK` | Verifies `status: "operational"`, 10 matches, 2,314 deliveries. |
| `GET` | `/api/v1/analytics/overview` | `tournament` (optional) | `200 OK` | Returns `matches_analyzed: 10`, `entities_analyzed: 116`, `apdi_records: 116`. |
| `GET` | `/api/v1/analytics/apdi` | `role_cohort`, `discrepancy_category`, `limit`, `offset` | `200 OK` | Preserves `null` `apdi_value` for `INSUFFICIENT_DATA` records. |
| `GET` | `/api/v1/analytics/apdi/{entity_id}` | `entity_id` (path) | `200 OK` / `404` | Returns 404 for unknown `player_invalid_999`. |
| `GET` | `/api/v1/matches` | `stage`, `date_from`, `date_to`, `limit`, `offset` | `200 OK` | Returns paginated list of matches. |
| `GET` | `/api/v1/matches/{match_id}/scorecard` | `match_id` (path) | `200 OK` / `404` | Innings 1 and 2 runs and wickets must match match totals. |
| `GET` | `/api/v1/players` | `team_id`, `role`, `query`, `limit`, `offset` | `200 OK` | Returns canonical player profiles. |
| `GET` | `/api/v1/articles` | `source_domain`, `language`, `limit`, `offset` | `200 OK` | Returns articles with provenance IDs. |
| `GET` | `/api/v1/topics/clusters` | None | `200 OK` | Returns all 3 topic clusters with keyword lists. |
| `GET` | `/api/v1/sources/provenance` | `limit`, `offset` | `200 OK` | Returns immutable source records with SHA-256 hashes. |

**How to Test API Routes**:
- Automated Test Suite: `pytest tests/test_api.py -v` (16 tests covering boundaries, pagination, 404s, 422s).
- Manual Test via curl:
  ```bash
  curl -s http://127.0.0.1:8000/api/v1/status | jq .
  curl -s "http://127.0.0.1:8000/api/v1/analytics/apdi?limit=5" | jq .
  curl -s http://127.0.0.1:8000/api/v1/matches/cric_20240629_ind_sou/scorecard | jq .
  ```

---

### Subsystem 7: Frontend UI & Client Integration

#### 7.1 `src/test/features.test.tsx` (Vitest + React Testing Library)
- **Test 1**: Verifies APDI Explorer renders entity rows with correct styling.
- **Test 2**: Confirms `INSUFFICIENT_DATA` rows render with `"unavailable"`, **never `"0.00"`**.
- **Test 3**: Verifies badge colors: `OVER_ATTENDED` (amber), `UNDER_ATTENDED` (indigo), `BALANCED` (emerald).
- **Test 4**: Verifies clicking "Inspect Lineage" triggers the entity detail drawer.

#### 7.2 `src/test/app.test.tsx`
- **Test 1**: Verifies navigation shell renders with all 7 required sidebar links (Overview, APDI, Matches, Players, Narratives, Topics, Sources).

---

## 3. End-to-End Testing & Verification Scenarios

### Scenario A: New Match Ingestion & Scorecard Integrity Gate
1. Supply a Cricsheet match JSON.
2. Ingest via `cricsheet_adapter`.
3. Assert database row counts: 1 match inserted, deliveries inserted = sum of balls in innings.
4. Call `GET /api/v1/matches/{match_id}/scorecard`:
   - Assert `innings1.total_runs == sum(deliveries where innings=1)`.
   - Assert `innings1.wickets == sum(is_wicket where innings=1)`.

### Scenario B: Editorial Ingestion & Deduplication Invariant
1. Ingest Wikipedia article `2024_Men's_T20_World_Cup_final.html`.
2. Assert article count increments by 1, paragraphs increment by 36.
3. Re-ingest the exact same HTML payload.
4. Assert return value is `(False, "Duplicate detected...")`.
5. Assert article count does not change.

### Scenario C: APDI Null-Propagation & Zero-Fabrication Gate
1. Create a dummy player with 2 balls faced and 0 editorial mentions.
2. Run `APDICalculator.compute_cohort_apdi()`.
3. Assert `record.apdi_value is None`.
4. Fetch via API `/api/v1/analytics/apdi`.
5. Inspect JSON: `"apdi_value": null`.
6. Inspect Frontend Table: Renders `unavailable`.
7. **Failure Condition**: Any display of `0.00` or classification of `BALANCED` is an automatic test failure.

---

## 4. Tester's Sign-Off Checklist

Before approving any release or PR, verify that every item below passes:

- [ ] `pytest tests/` passes **112 / 112 tests** with 0 errors.
- [ ] `npm run test` in `frontend/` passes **9 / 9 tests**.
- [ ] `npm run typecheck` in `frontend/` reports **0 errors**.
- [ ] `npm run build` in `frontend/` completes successfully.
- [ ] `scripts/validate_raw_matches_against_db.py` reports **10 / 10 matches passed** with 100% delivery parity.
- [ ] `scripts/evaluate_nlp_gold_set.py` reports **0 false associations (0.0% error rate)**.
- [ ] `scripts/phase9_apdi_sensitivity.py` runs and confirms **13 Valid / 103 Insufficient Data**.
- [ ] Browser smoke test at `http://127.0.0.1:5173/`: all pages load, no console errors, APDI table renders correctly.
