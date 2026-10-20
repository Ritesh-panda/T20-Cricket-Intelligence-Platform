# Architecture Decision Records (ADRs) & Trade-off Log

## 1. Context & Purpose

This document records key architectural, data engineering, and machine learning decisions made for the T20 Cricket Intelligence Platform, articulating the context, alternatives considered, chosen direction, and trade-offs.

---

## 2. Completed Architecture Decision Records

### ADR-001: Local-First Architecture vs. Cloud / Distributed Infrastructure
- **Status**: ACCEPTED
- **Context**: The project requires modular ingestion, NLP, and analysis of ICC Men's T20 World Cup tournaments. Initial architectures could introduce Apache Spark, Kafka, distributed vector databases (Pinecone/Milvus), and Kubernetes.
- **Decision**: Adopt a strict **local-first** architecture. Run data pipelines via Python scripts, store structured data in SQLite/PostgreSQL and local Parquet files, compute embeddings using local PyTorch/ONNX models, and serve via local FastAPI and React.
- **Consequences**:
  - *Positive*: Zero cloud hosting costs, zero credential exposure risk, deterministic reproducibility, rapid developer onboarding, testable in standard CI.
  - *Negative*: Scale is bounded by host machine RAM and disk (sufficient for multiple World Cups, totaling tens of thousands of articles and commentary lines).

---

### ADR-002: Storage Layer Strategy (Relational + Columnar Parquet vs. Dedicated Vector Database)
- **Status**: ACCEPTED
- **Context**: Unstructured documents require semantic retrieval and clustering. We evaluated using a dedicated vector database (Chroma, Qdrant, Weaviate) versus storing embeddings directly in Parquet/NumPy alongside relational metadata.
- **Decision**: Use a **hybrid multi-tier storage model**:
  1. *Tier 1 (Raw Archive)*: Compressed immutable JSONL/HTML files.
  2. *Tier 2 (Relational Metadata)*: SQLite (or local PostgreSQL) for transactional state, match metadata, entity links.
  3. *Tier 3 (Columnar Datasets)*: Apache Parquet for bulk deliveries, paragraphs, and 384-d vector embeddings.
  4. *Vector Index*: Use in-memory cosine similarity (Scikit-Learn / FAISS CPU) over local Parquet arrays rather than running a persistent vector DB daemon.
- **Consequences**:
  - *Positive*: Minimal dependency footprint; datasets can be inspected with simple Python / DuckDB queries.
  - *Negative*: Approximate nearest neighbor indexing across millions of vectors is slower than dedicated vector servers (irrelevant at tournament scale of <100,000 vectors).

---

### ADR-003: Comparative Topic Modeling Matrix vs. Single Assumed Model
- **Status**: ACCEPTED
- **Context**: Often projects prematurely commit to a single technique (e.g., jumping directly to BERTopic or LDA).
- **Decision**: Implement a **4-model comparative experimental matrix** on the identical test corpus:
  1. TF-IDF + K-Means (Lexical baseline)
  2. Dense Sentence Embeddings + K-Means (Dense fixed baseline)
  3. Dense Sentence Embeddings + UMAP + HDBSCAN (Density & outlier-aware)
  4. BERTopic (Interpretable c-TF-IDF topic modeling)
- **Consequences**:
  - *Positive*: Directly satisfies research rigor; enables objective evaluation of cluster coherence, outlier rate, and interpretability.
  - *Negative*: Requires implementing and maintaining pipeline abstractions across 4 configurations.

---

### ADR-004: Article Ingestion Tooling (Trafilatura + BS4 vs. Headless Browser Automation)
- **Status**: ACCEPTED
- **Context**: Ingesting web articles can be done via fast HTTP requests with text extraction libraries (Trafilatura) or heavyweight browser automation (Playwright/Selenium).
- **Decision**: Standardize on **Trafilatura with BeautifulSoup4 DOM fallbacks** over polite HTTP requests (`requests`/`httpx`). Keep Playwright optional and restricted only to dynamic single-page applications where static HTML extraction fails completely and terms permit.
- **Consequences**:
  - *Positive*: High speed (50ms vs 3000ms per article), minimal CPU/RAM overhead, fewer browser binary dependencies.
  - *Negative*: Cannot execute complex JavaScript-driven dynamic pagination unless RSS/sitemap feeds are leveraged.

---

### ADR-005: Grounding Match Facts in Cricsheet Open Data
- **Status**: ACCEPTED
- **Context**: Ground-truth match deliveries and scorecards could be scraped from media publishers or ingested from structured open databases.
- **Decision**: Designate **Cricsheet** (ODbL/CC-BY) as the canonical match fact authority.
- **Consequences**:
  - *Positive*: High fidelity, verified delivery-by-delivery outcomes, zero scraping risk, legal clarity.
  - *Negative*: Media publishers occasionally use slight spelling variations or ball-numbering quirks compared to Cricsheet, requiring robust entity resolution.

---

## 3. Unresolved Design Decisions & Explicit Trade-offs

The following design decisions are documented with their respective trade-offs, awaiting user preferences and candidate repository audits:

### Decision U-01: Default Relational Backend — SQLite vs. PostgreSQL
- **Option A (SQLite with WAL mode)**:
  - *Pros*: Zero external service dependencies, single-file database (`cricket.db`), easiest local development.
  - *Cons*: Limited concurrent write throughput during parallel crawling.
- **Option B (PostgreSQL)**:
  - *Pros*: Robust concurrency, rich JSONB indexing, full-text search operators (`tsvector`).
  - *Cons*: Requires running Docker container or local PostgreSQL installation.
- **Recommendation**: Support **SQLite by default** for instant out-of-the-box local operation, with SQLAlchemy schema designed to seamlessly switch to PostgreSQL via `DATABASE_URL`.

---

### Decision U-02: Commentary and News Corpus Clustering Strategy
- **Option A (Independent Intra-Corpus Clustering First, then Cluster-to-Cluster Association)**:
  - *Pros*: Prevents document-length asymmetry distortions (1000-word articles vs. 20-word commentary lines); respects unique vocabulary distributions.
  - *Cons*: Requires an extra step to link news clusters to commentary clusters.
- **Option B (Joint Shared-Embedding Space Clustering)**:
  - *Pros*: Directly reveals cross-source thematic convergence in a single space.
  - *Cons*: High risk that commentary forms massive isolated micro-clusters due to domain brevity, dominating cluster count.
- **Recommendation**: Follow **Option A**: evaluate news and commentary separately first, then benchmark cross-corpus alignment.

---

### Decision U-03: Dashboard Architecture — React+Vite+Tailwind SPA vs. Streamlit Rapid Prototype
- **Option A (React + TypeScript + Vite + Tailwind CSS + FastAPI)**:
  - *Pros*: State-of-the-art sports analytics UI, custom timeline visualizations, highly responsive, production-ready portfolio piece.
  - *Cons*: Requires Node.js toolchain and managing frontend/backend repositories.
- **Option B (Streamlit)**:
  - *Pros*: 100% Python, rapid initial prototyping of charts.
  - *Cons*: Clunky UI, full-page re-renders, limited interactive timeline manipulation, feels like a basic prototype.
- **Recommendation**: Implement **React + TypeScript + FastAPI** to deliver the requested polished sports intelligence product.
