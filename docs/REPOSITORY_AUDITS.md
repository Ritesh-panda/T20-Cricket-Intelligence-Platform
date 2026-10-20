# Repository Audit Methodology & Assessment Framework

## 1. Audit Purpose & Guiding Principles

This document formalizes the systematic evaluation framework applied to any third-party open-source repository proposed for the T20 Cricket Intelligence Platform.

We do not blindly clone, execute, or merge external code. Each candidate repository is subjected to a formal 5-pillar audit before code is integrated or adapted into the primary codebase.

---

## 2. The 5-Pillar Evaluation Rubric

Every candidate repository is scored across five criteria on a scale of 1 (Unacceptable) to 5 (Exemplary):

### Pillar 1: Legal & License Compatibility
- **Evaluation**: Permissive licenses (MIT, Apache 2.0, BSD 2/3-Clause, ISC) are preferred. Restrictive copyleft (GPL v2/v3, AGPL) must be strictly isolated to prevent viral infection of core assets. Commercial/academic restrictions must be assessed.
- **Red Flags**: Unlicensed code ("All rights reserved"), conflicting licenses, or scrapers explicitly marketed to defeat site protections or scrape copyright-infringing streams.

### Pillar 2: Security & Supply Chain Hygiene
- **Evaluation**: Automated scan of dependencies (`requirements.txt`, `poetry.lock`, `package.json`) for known CVEs. Check for obfuscated code, dangerous runtime calls (`eval`, `exec`, unverified `pickle.load`), hardcoded API keys/passwords, or undeclared outbound telemetry.
- **Red Flags**: Outdated packages with critical vulnerabilities; attempts to inject custom binaries.

### Pillar 3: Architectural Modularity & Clean Interfaces
- **Evaluation**: Does the repository separate concerns (e.g., crawler decoupled from storage and analytics)? Are data schemas typed and clearly documented? Can extraction logic be extracted as a standalone utility without dragging in an entire framework?
- **Red Flags**: Spaghetti monolithic scripts mixing database queries, web scraping, and Matplotlib plotting in a single file without functions or classes.

### Pillar 4: Code Quality, Robustness & Tests
- **Evaluation**: Presence of automated unit/integration tests (Pytest), linting (Ruff/Flake8), type annotations (mypy), and graceful error handling (network retries, timeouts, malformed HTML fallbacks).
- **Red Flags**: Zero test suite, bare `except: pass` exception swallowing, hardcoded absolute local paths (`C:\Users\username\...`).

### Pillar 5: Maintenance Status & Technical Debt
- **Evaluation**: Recency of last commit, responsiveness to issues/PRs, compatibility with modern runtimes (Python 3.11+, Pydantic v2, recent Pandas/Scikit-Learn).
- **Red Flags**: Abandoned repos (>3 years inactive) relying on deprecated libraries (e.g., Python 2, old TensorFlow 1.x, discontinued scraping APIs).

---

## 3. Decision Framework & Action Criteria

| Decision | Criteria | Action Required |
| :--- | :--- | :--- |
| **REUSE** | Score >= 20/25. Permissive license, high test coverage, clean modular interface, directly fills a target module requirement. | Import as a tracked sub-module or vendor clean module under `src/adapters/` or `src/nlp/` with original license & copyright header preserved. |
| **ADAPT** | Score 14–19/25. Core algorithm, regex, or parsing heuristic is brilliant and sound, but code is poorly structured or tightly coupled to obsolete schemas. | Extract essential algorithmic logic into our canonical Pydantic architecture. Refactor and write comprehensive unit tests. Attribute original authors. |
| **REFERENCE ONLY** | Score 10–13/25. Useful conceptual design, domain-specific gazetteer, or regex pattern, but code quality or licensing prohibits inclusion. | Study mathematical or analytical formulation; re-implement cleanly from scratch within our own architectural standards. |
| **REJECT** | Score < 10/25, or ANY red-flag violation in Pillar 1 or 2. | Do not use. Document explicit rationale in `REPOSITORY_AUDITS.md` and recommend alternative open-source or custom approach. |

---

## 4. Repository Audit Template

When candidate repository links are provided, the audit team will populate the following structured card for each repository:

```markdown
### [Audit-XXX] {Repository Name}
- **Upstream URL**: https://github.com/{owner}/{repo}
- **Evaluated Commit**: `{git-hash}`
- **License**: `{License Type}` (Verified in repo LICENSE file)
- **Primary Domain**: {e.g. Scraper / Commentary Parser / Analytics / Topic Model}

#### 1. Technical Analysis
- **Core Capabilities**: {Summary of features}
- **Dependencies & Footprint**: {Key libraries required}
- **Identified Limitations / Technical Debt**: {Flaws, missing tests, anti-patterns}
- **Security Assessment**: {Safety check results}

#### 2. Rubric Scoring
| Pillar | Score (1-5) | Justification |
| :--- | :---: | :--- |
| 1. Licensing | X/5 | ... |
| 2. Security | X/5 | ... |
| 3. Architecture | X/5 | ... |
| 4. Code Quality | X/5 | ... |
| 5. Maintenance | X/5 | ... |
| **Total** | **XX/25** | |

#### 3. Audit Decision & Integration Strategy
- **Decision**: [REUSE / ADAPT / REFERENCE ONLY / REJECT]
- **Rationale**: {Why this decision was made}
- **Target Modules in Platform**: {e.g., Module C - Commentary Parsing}
- **Refactoring & Adaptation Plan**: {Specific changes required to integrate}
- **Attribution & Notice Requirements**: {Text required in LICENSES.md}
```
