# T20 Cricket Intelligence Platform
### Open-Source Research, Narrative Discovery & Event Grounding for the Men's T20 World Cup

An end-to-end sports intelligence and NLP research system that bridges the gap between **unstructured cricket media (news articles, expert analysis, ball-by-ball written commentary)** and **structured match facts (deliveries, wickets, phases from Cricsheet)**.

---

## 📖 Project Documentation Suite

The complete architectural, research, and data specifications have been prepared under the [`docs/`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs) directory:

1. [PROJECT_BLUEPRINT.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/PROJECT_BLUEPRINT.md) — Platform vision, core research questions, and architectural principles.
2. [REQUIREMENTS.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/REQUIREMENTS.md) — Functional (FR-A to FR-L) and non-functional requirements.
3. [ARCHITECTURE.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/ARCHITECTURE.md) — System decomposition, Mermaid data flow diagrams, and local-first execution layout.
4. [DATA_MODEL.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/DATA_MODEL.md) — Canonical schemas (Matches, Deliveries, Articles, Commentary, Alignments, Entities).
5. [SOURCE_REGISTER.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SOURCE_REGISTER.md) — Data source inventory (Cricsheet, Cricbuzz, ESPNcricinfo, Wisden) and upstream repository registry.
6. [REPOSITORY_AUDITS.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/REPOSITORY_AUDITS.md) — 5-pillar repository audit rubric, scoring system, and evaluation template.
7. [RESEARCH_PLAN.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/RESEARCH_PLAN.md) — Experimental model matrix (TF-IDF, Embeddings, HDBSCAN, BERTopic) and alignment formulation.
8. [EVALUATION_PLAN.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/EVALUATION_PLAN.md) — Quantitative metrics (Silhouette, Davies-Bouldin, Coherence, Outlier rate, Precision/Recall/MRR) and intrusion tests.
9. [SECURITY_AND_LICENSING.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SECURITY_AND_LICENSING.md) — Permitted access, robots.txt compliance, copyright/fair use, and secret hygiene.
10. [IMPLEMENTATION_ROADMAP.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/IMPLEMENTATION_ROADMAP.md) — 9-phase milestone delivery plan with formal completion gates.
11. [DECISIONS.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/DECISIONS.md) — Architecture Decision Records (ADRs) and unresolved trade-offs.
12. [SESSION_JOURNAL.md](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SESSION_JOURNAL.md) — Chronological developer journal tracking daily steps, tests, and findings.

---

## 🏛️ System Overview

```
[01. Source Registry & Adapters]
  └── Cricsheet Open Data + Permitted Publishers (Robots.txt compliant, rate-limited)
        │
[02. Extraction, Normalization & Validation]
  └── Trafilatura text extraction + Commentary parsing + Pydantic v2 validation + SHA-256 deduplication
        │
[03. Canonical Cricket Data Layer]
  └── SQLite / PostgreSQL metadata + Parquet columnar datasets (local-first)
        │
[04. Cricket NLP & Match Analytics]
  └── Cricket NER & gazetteer entity resolution + Aspect sentiment + Sentence Transformers
        │
[05. Reasoning, Clustering & Event Alignment]
  └── Comparative Topic Models (TF-IDF / HDBSCAN / BERTopic) + Hybrid media-to-match event linker
        │
[06. Serving & Presentation]
  └── FastAPI backend service + React/TypeScript sports intelligence dashboard
```

---

## 🔬 Core Research Hypotheses

- **Unsupervised Topic Discovery**: Uncover recurring T20 themes (death-overs bowling, powerplay collapse, selection debates) without rigid manual taxonomies.
- **Cross-Vocabulary Equivalence**: Dense sentence embeddings cluster articles reporting the same match event despite publisher stylistic differences.
- **Media-to-Match Grounding**: Link subjective news assertions to exact delivery sequences (e.g., Over 17.1–17.6) with measured precision and recall.
- **Narrative vs Performance**: Quantify media hype vs. objective on-field impact using an Attention-to-Performance Ratio ($APR$).

---

## 🛡️ Repository Isolation Policy

All candidate third-party open-source repositories will be cloned into the local quarantined directory:
```
research_sources/   <-- Excluded from Git via .gitignore
```
Candidate repositories are inspected in read-only mode for commit hash, license, dependencies, and code quality before any logic is reused or adapted.

---

## 🚀 Current Status & Next Checkpoint

- **Phase 0 (Initialization & Blueprint)**: **COMPLETE** ✅
- **Phase 1 (Repository Audits)**: **AWAITING URL LIST** ⏳
- **Next Action**: User to provide curated list of open-source repository URLs to begin Phase 1 audits and classification.
