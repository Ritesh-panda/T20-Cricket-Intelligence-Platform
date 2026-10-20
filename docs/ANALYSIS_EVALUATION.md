# Phase 5 Analysis & Topic Evaluation Report

## 1. Evaluation Methodology

The Phase 5 semantic analysis, clustering, and narrative alignment modules were evaluated against curated deterministic test fixtures in `tests/test_analysis.py`.

> [!IMPORTANT]
> **Fixture vs Real-World Corpus Metrics**:
> In accordance with project governance, all metrics reported below reflect performance on curated ground-truth test fixtures and deterministic test doubles. They are not fabricated real-world tournament findings.

---

## 2. Quantitative Evaluation Benchmarks

### 2.1 Embedding Test Double Benchmark
- **Model**: `DeterministicTestEmbeddingModel` (384-dimensional unit vectors).
- **Dimension Invariant**: 100.0% of vectors have shape `(N, 384)` with `float32` dtype.
- **L2-Norm Invariant**: $\|v\|_2 = 1.0 \pm 10^{-5}$ across all non-empty inputs.
- **Empty String Invariant**: Empty / whitespace-only inputs evaluate to zero vectors ($0.0$).
- **Deterministic Repeatability**: Identical texts produce identical vectors across separate runs ($100.0\%$).

### 2.2 Sparse TF-IDF Syntax Preservation Benchmark
- Evaluated on required project edge cases in `tests/test_analysis.py`:
  - `19.4 Bumrah to Kohli, SIX!` $\to$ Token `19.4` preserved.
  - `Kohli scored 82* from 53 balls.` $\to$ Token `82*` preserved without trailing word boundary corruption.
  - `India finished on 182/5 after 20 overs.` $\to$ Token `182/5` preserved.
  - `Overturned after DRS.` $\to$ Token `drs` preserved.

### 2.3 Topic Clustering Benchmark (K-Means & DBSCAN)
- **K-Means Seed Reproducibility**: 100% label parity between runs under `random_state=42`.
- **DBSCAN Noise Tagging**: 100% of isolated outlier points are tagged as `-1` and labeled as `"Outliers / Noise"`.
- **Silhouette Score**: Evaluated on separated geometric clusters $\to \text{Silhouette} > 0.50$.
- **Graceful Undefined Handling**: When $N < 2$ or all points are noise, Silhouette and Davies-Bouldin indices are gracefully omitted with an explanatory note.

### 2.4 Two-Stage Cross-Source Alignment Benchmark
- **Candidate Retrieval**: Stage 1 retrieves semantic neighbors above minimum threshold.
- **Entity Context Re-Ranking**: Stage 2 rewards shared named entities (+0.35 max bonus).
- **Conservative Gating**: Passages describing the same delivery with matching actors are marked `ACCEPTED`; passages with weak semantic overlap or mismatched entities are marked `NEEDS_REVIEW` or `UNRESOLVED`.

### 2.5 Narrative Timeline Benchmark
- **Observed vs Inferred Distinction**: 100% accuracy in separating articles with ISO timestamps (`observed_timestamps_count`) from untimed articles (`inferred_timestamps_count` in `unknown_date` bucket).
- **Volume & Sentiment Aggregation**: Accurately aggregates mean sentiment and topic distributions per day bucket.

---

## 3. Storage and Idempotency Verification

- **Schema Migration**: Fresh and pre-existing SQLite databases seamlessly initialize Schema Version 4 (`embedding_records`, `topic_runs`, `topic_clusters`, `topic_assignments`, `cross_source_matches`, `timeline_snapshots`).
- **Embedding Pipeline Idempotency**:
  - Run 1 on 1 document $\to 1$ embedding computed, 0 skipped.
  - Run 2 on unchanged document $\to 0$ embeddings computed, 1 skipped cache hit.
- **Empty Database Reporting**: `analysis-stats`, `cluster-topics`, `narrative-timeline`, and `evaluate-topics` report 0 records truthfully without fabricating synthetic counts.

---

## 4. Test Suite Execution

To run all 71 tests in the repository:
```powershell
pytest tests -v
```

To run only the Phase 5 analysis test suite:
```powershell
pytest tests/test_analysis.py -v
```

To validate storage invariants:
```powershell
python -m src.pipeline analysis-validate
```
