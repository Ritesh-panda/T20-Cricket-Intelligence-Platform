# FastAPI Research Backend Package

This directory contains the production-grade FastAPI REST backend for the **T20 Cricket Intelligence Platform**.

## Package Structure
- `main.py`: Application factory (`create_app`), middleware setup, lifespan handlers.
- `config.py`: Configuration models and environment bindings (`APISettings`).
- `dependencies.py`: FastAPI dependency providers for storage, preflight, and calculators.
- `errors.py`: Safe centralized exception handlers and standardized `ErrorResponse` schema.
- `routes/`: Modular endpoints:
  - `health.py`: Application liveness, persistence readiness, and system data sufficiency.
  - `matches.py`: Canonical match queries, ball-by-ball deliveries, and performance scorecards.
  - `players.py`: Player identity records with alias matching.
  - `teams.py`: Team identity records and search.
  - `articles.py`: Editorial article metadata, full texts, and paragraph partitions.
  - `commentary.py`: Ball-by-ball commentary records.
  - `nlp.py`: Topic clusters, entity mentions, narrative timeline, and cross-source alignments.
  - `analytics.py`: Media attention, performance scores, narrative framing, and APDI metrics.
  - `observability.py`: Ingestion runs, provenance audits, and pipeline metrics.
- `schemas/`: Pydantic response models ensuring typed, validated outputs.

## Running the API Locally
```bash
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```
Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

For complete endpoint specifications, refer to [API_DOCUMENTATION.md](../../docs/API_DOCUMENTATION.md).
