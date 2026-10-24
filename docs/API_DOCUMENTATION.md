# Phase 6B — FastAPI Backend & Research REST API Documentation

## 1. Overview & Architecture

The **FastAPI Research API** exposes the analytical, editorial, and canonical cricket data layers developed across Phases 1 through 6A through a production-grade, documented, type-safe REST interface.

The API is strictly **read-only**, parameterized against SQL injection, and structured around the following design principles:

1. **Separation of Concerns**:
   - `src/api/main.py`: Application factory, middleware lifecycle, and route mounting.
   - `src/api/config.py`: Environment-backed configuration using `pydantic-settings`.
   - `src/api/dependencies.py`: Dependency injection for storage managers, preflight validators, and analytics calculators.
   - `src/api/errors.py`: Standardized error responses (`ErrorResponse`) preventing database exception leaks or stack traces.
   - `src/api/routes/`: Distinct route modules organized by entity and capability family.
   - `src/api/schemas/`: Explicit request/response Pydantic schemas validating pagination and entity payloads.
2. **Data Integrity & Truthful Empty States**:
   - Empty database states return HTTP 200 with `items: []`, `total: 0`, and `has_more: false`.
   - Nonexistent IDs return HTTP 404 with structured `ResourceNotFound` error details.
   - Incomplete analytical evidence preserves `INSUFFICIENT_DATA` with `null` APDI scores. No numerical scores are ever fabricated.
3. **Security & Restrictive Defaults**:
   - CORS origin whitelist configured via environment (defaults to `localhost:3000` and `localhost:5173`). Wildcard `*` is never combined with credentials.
   - All SQL queries use parameterized arguments (`?`), preventing SQL injection.
   - Read-only surface: no destructive or ingestion write operations are exposed over the public API.

---

## 2. Local Startup & Configuration

### Startup Command
Run the local development server with live reload:
```bash
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```
Or with Python module invocation:
```bash
python -m uvicorn src.api.main:app --reload
```

### Interactive Documentation
Once the server is running:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

### Environment Variables
Configure through `.env` or system environment variables:
| Variable | Default | Description |
|---|---|---|
| `DB_PATH` | `data/cricket_intel.db` | Absolute or relative path to SQLite database |
| `DEFAULT_TOURNAMENT` | `T20 World Cup 2024` | Default tournament scope for analytics |
| `CORS_ORIGINS` | `["http://localhost:3000", "http://localhost:5173"]` | JSON list or comma-delimited allowed origins |
| `DEFAULT_PAGE_LIMIT` | `20` | Default items returned per page |
| `MAX_PAGE_LIMIT` | `100` | Maximum allowable limit per request |
| `DEBUG` | `false` | Enable verbose debug logging |

---

## 3. Standardized Response Formats

### Pagination Wrapper
All collection endpoints return a standardized envelope:
```json
{
  "items": [ ... ],
  "pagination": {
    "total": 42,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

### Error Response Envelope
All 4xx and 5xx errors return a consistent envelope without leaking stack traces or internal schema details:
```json
{
  "error": "ResourceNotFound",
  "message": "matches with ID 'm_unknown' was not found.",
  "detail": null,
  "timestamp_utc": "2026-10-24T12:00:00Z"
}
```

---

## 4. Complete Endpoint Inventory

### 1. Health & System Readiness
| Method | Endpoint | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/health` | Process liveness probe | None |
| `GET` | `/ready` | Database accessibility and schema version probe | None |
| `GET` | `/api/v1/status` | Dataset availability, platform capabilities, and analytics sufficiency | `tournament` (str) |

### 2. Matches & Cricket Performance
| Method | Endpoint | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/api/v1/matches` | List paginated matches | `tournament`, `season`, `team_id`, `limit`, `offset` |
| `GET` | `/api/v1/matches/{match_id}` | Retrieve single match metadata | None |
| `GET` | `/api/v1/matches/{match_id}/deliveries` | List granular ball-by-ball deliveries | `innings`, `over_num`, `phase`, `limit`, `offset` |
| `GET` | `/api/v1/matches/{match_id}/performance` | Match scorecard with batting & bowling performance | None |

### 3. Players & Teams
| Method | Endpoint | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/api/v1/players` | List canonical players with alias resolution | `team_id`, `search`, `limit`, `offset` |
| `GET` | `/api/v1/players/{player_id}` | Retrieve single canonical player | None |
| `GET` | `/api/v1/teams` | List canonical teams | `search`, `limit`, `offset` |
| `GET` | `/api/v1/teams/{team_id}` | Retrieve single canonical team | None |

### 4. Articles & Commentary
| Method | Endpoint | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/api/v1/articles` | List news articles with metadata | `source_domain`, `language`, `limit`, `offset` |
| `GET` | `/api/v1/articles/{article_id}` | Full article including text body and provenance | None |
| `GET` | `/api/v1/articles/{article_id}/paragraphs` | Ordered paragraph segments for an article | `limit`, `offset` |
| `GET` | `/api/v1/commentary` | List ball-by-ball commentary | `match_id`, `innings`, `over_num`, `source_domain`, `limit`, `offset` |
| `GET` | `/api/v1/commentary/{commentary_id}` | Retrieve single commentary entry | None |

### 5. NLP, Topics & Narrative Intelligence
| Method | Endpoint | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/api/v1/topics` | List discovered topic clusters with keywords | `run_id`, `limit`, `offset` |
| `GET` | `/api/v1/topics/{topic_id}` | Single topic cluster record | None |
| `GET` | `/api/v1/entities` | List fine-grained entity mentions and resolution status | `entity_type`, `resolution_status`, `resolved_id`, `source_type`, `limit`, `offset` |
| `GET` | `/api/v1/narratives/timeline` | Narrative evolution snapshots over time | `limit`, `offset` |
| `GET` | `/api/v1/narratives/matches` | Cross-source alignment links between editorial & commentary | `status`, `match_id`, `limit`, `offset` |

### 6. Analytics & APDI
| Method | Endpoint | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/api/v1/analytics/overview` | High-level summary of APDI distributions & preflight status | `tournament` (str) |
| `GET` | `/api/v1/analytics/attention` | Media attention metrics and prominence scores | `tournament`, `entity_id`, `limit`, `offset` |
| `GET` | `/api/v1/analytics/performance` | Objective performance scores derived from deliveries | `tournament`, `entity_id`, `role`, `limit`, `offset` |
| `GET` | `/api/v1/analytics/framing` | Entity-targeted sentiment & publisher framing variance | `entity_id` (str, required) |
| `GET` | `/api/v1/analytics/apdi` | Attention-to-Performance Discrepancy Index records | `tournament`, `role_cohort`, `discrepancy_category`, `limit`, `offset` |
| `GET` | `/api/v1/analytics/apdi/{entity_id}` | Latest APDI evaluation for a player or team | None |
| `GET` | `/api/v1/analytics/validation` | Structural invariant validation across Phase 6A tables | None |

### 7. Observability & Provenance
| Method | Endpoint | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/api/v1/observability/ingestion-runs` | Ingestion pipeline audit records | `status`, `limit`, `offset` |
| `GET` | `/api/v1/observability/sources` | Immutable harvest provenance records (no credentials) | `source_name`, `limit`, `offset` |
| `GET` | `/api/v1/observability/pipeline-stats` | Aggregated crawler and storage entity statistics | `source_id` (str) |
| `GET` | `/api/v1/observability/analytics-runs` | Analytical batch execution audit records | `tournament`, `limit`, `offset` |
