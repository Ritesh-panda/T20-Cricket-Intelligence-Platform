# Data Quality, Ingestion Metrics & Honest Coverage Reporting

## 1. Principles of Honest Coverage

A core principle of the T20 Cricket Intelligence Platform is **empirical transparency**:

> **Honest Coverage Rule**: An inaccessible or partially acquired source must never appear fully ingested. The system never claims that the Men's T20 World Cup corpus is complete unless measured historical coverage against official tournament fixtures mathematically confirms that state.

The pipeline reports:
- Number of tournament matches scheduled vs. number of matches ingested with validated delivery scorecards.
- Number of URLs discovered vs. number of URLs successfully fetched and parsed.
- Exact failure counts, HTTP status breakdowns, and error diagnostics.
- Clear distinction between skipped identical duplicates and legitimate content updates.

---

## 2. Data Quality Dimensions & Verification Invariants

| Quality Dimension | Enforcement Mechanism | Failure Action |
| :--- | :--- | :--- |
| **Scorecard Total Runs Invariant** | Pydantic validator on `DeliveryRecord`: `total_runs == batter_runs + extra_runs` | Rejects delivery record with `ValueError` |
| **Wicket Dismissal Invariant** | Pydantic validator on `DeliveryRecord`: `is_wicket == True` requires non-null `player_dismissed_id` | Rejects delivery record with `ValueError` |
| **Score Reconciliation** | `CricsheetAdapter` sums runs and wickets per innings and reconciles with match winner and margin | Generates structured `ScoreReconciliationReport` with discrepancy warnings |
| **Audit Provenance Invariant** | `SourceRecord.content_hash_sha256` validated against regex `^[0-9a-fA-F]{64}$` | Rejects unhashed or malformed audit records |
| **Relational Integrity** | SQLite Foreign Key enforcement: deliveries must link to `matches`, commentary to `matches`, paragraphs to `articles`, and entities to `source_records` | Aborts transaction with `IntegrityError` if foreign key parent missing |
| **URL Deduplication** | `discovered_urls.canonical_url UNIQUE` and `articles.canonical_url UNIQUE` | Skips duplicate without creating orphan or fragmented database IDs |
| **Content Hash Deduplication** | `articles.raw_content_hash UNIQUE` | Skips identical text fetched from alternate or mirrored URLs |

---

## 3. Ingestion Metrics & Observability

The platform produces operational metrics per source:

- **URLs Discovered**: Total count of canonical URLs identified across feeds, sitemaps, and indices.
- **Fetch Attempts & Successes**: Cumulative HTTP attempts vs. HTTP 200/304 successful responses.
- **HTTP Failures**: HTTP 4xx (client/rate-limit) and 5xx (server error) counts.
- **Parsing & Validation Failures**: DOM extraction or Pydantic schema validation failures.
- **Records Ingested, Skipped & Updated**:
  - `Ingested`: Newly persisted records.
  - `Skipped`: Identical content hash or 304 Not Modified.
  - `Updated`: Legitimate content revision applied to existing canonical URL (with entry in `article_revisions`).
- **Processing Duration**: Wall-clock execution time per source.

Metrics are viewed via:
```bash
python -m src.pipeline stats [--source <source_id>]
```

---

## 4. Database Validation CLI

To check the relational health of previously ingested records at any time:
```bash
python -m src.pipeline validate
```

The validation command verifies:
1. Delivery totals integrity across all innings.
2. Deliveries linked to existing matches (no orphaned deliveries).
3. Articles segmented into valid paragraphs.
4. Commentary entries linked to matches.

---

## 5. Failure Recovery & Inspection Protocol

When network interruptions or publisher rate limits occur:
1. Run `python -m src.pipeline inspect-failed` to review failed URLs and their error diagnostics.
2. Run `python -m src.pipeline run --resume` to automatically reset `RETRY_PENDING` and `FAILED` records back to `QUEUED` and resume from the last successful checkpoint.
