# Phase 9 Source Legality, Licensing, and Acquisition Strategy Audit

**Audit Date**: 2026-10-24  
**Project**: T20 Cricket Intelligence Platform  
**Status**: Comprehensive Source Audit & Provenance Protocol  

---

## 1. Executive Summary & Legal Principles

The **T20 Cricket Intelligence Platform** operates under a strict research compliance mandate. As an academic/empirical research system investigating the relationship between media attention and athletic performance, data acquisition must adhere to copyright law, terms of service (ToS), `robots.txt` directives, and open-source licenses.

### 1.1 Non-Negotiable Boundaries
1. **No Paywall / Access Evasion**: The platform will never bypass paywalls, authentication cookies, CAPTCHAs, Cloudflare challenge pages, or user-agent fingerprinting.
2. **Robots.txt is a Technical Restriction, Not a Content License**: A `robots.txt` allowing indexing does **not** grant copyright permission to scrape, store, embed, or redistribute full editorial prose.
3. **Open Access Does Not Mean Public Domain**: Freely readable articles on the open web remain protected by copyright unless explicitly licensed under permissive terms (e.g., Creative Commons).
4. **Metadata vs. Full-Text Segregation**: Syndicated headlines, titles, publication dates, and canonical URLs are fair reference facts, but full article bodies may only be ingested and embedded when an express permissive license exists.
5. **Precautionary Classification**: Any source whose licensing terms are ambiguous, unstated, or restrictive is categorized as `REQUIRES_PERMISSION` and withheld from automated ingestion.

---

## 2. Comprehensive Source Audit Matrix

Every current and candidate data source evaluated for the platform is audited below across 11 compliance dimensions.

### 2.1 Current Ingested Sources (Tier A & Tier B)

#### Source 1: Cricsheet (Tier A — Structured Cricket Match Data)
- **Provider & Canonical URL**: Cricsheet (`https://cricsheet.org/`)
- **Content Type**: Structured match ball-by-ball deliveries, lineups, match officials, and scores.
- **License / Permission Basis**: **Open Data Commons Attribution License (ODC-By 1.0)** / **Creative Commons Attribution 4.0 (CC BY 4.0)**.
- **Terms of Use & Robots Directives**: Unrestricted bulk download archives provided intentionally for public and research use. `robots.txt` permits access to `/downloads/`.
- **Permitted Acquisition Method**: Automated HTTP `GET` of versioned `.zip` archives (e.g., `t20s_male_json.zip`).
- **Attribution Requirements**: Mandatory attribution: *"Data provided by Cricsheet (cricsheet.org), licensed under ODC-By 1.0."*
- **Permissions Audit**:
  - Raw Text / JSON Storage: **PERMITTED**
  - Processing & Ingestion: **PERMITTED**
  - Vector Embedding: N/A (structured data)
  - Database Redistribution: **PERMITTED** (with license preservation)
- **Date & Method of Verification**: 2026-10-24; Verified against official site terms (`https://cricsheet.org/license/`).
- **Restrictions / Notes**: Static caching only; refresh on new tournament release.

#### Source 2: Wikimedia / Wikipedia (Tier B — Reference & Tournament Overviews)
- **Provider & Canonical URL**: Wikimedia Foundation (`https://en.wikipedia.org/`)
- **Content Type**: Encyclopedic tournament overviews, squad lists, team histories, match summaries.
- **License / Permission Basis**: **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)** and **GNU Free Documentation License (GFDL)**.
- **Terms of Use & Robots Directives**: Permitted via official MediaWiki REST API (`/api/rest_v1/page/html/`) with polite custom `User-Agent`.
- **Permitted Acquisition Method**: Official REST API query with rate-limiting ($\le 1.0$ request/sec).
- **Attribution Requirements**: Mandatory page title, canonical URL, MediaWiki revision ID, and CC BY-SA 4.0 attribution statement.
- **Permissions Audit**:
  - Raw HTML Storage: **PERMITTED**
  - Processing & Paragraph Segmentation: **PERMITTED**
  - Dense Vector Embedding: **PERMITTED** (transformative research derivative)
  - Redistribution: **PERMITTED under CC BY-SA 4.0**
- **Date & Method of Verification**: 2026-10-24; Verified MediaWiki headers (`dc:modified`, `ETag`, revision ID).
- **Restrictions / Notes**: **Content scope limitation**: Wikimedia content is encyclopedic and retrospective; it does not constitute contemporary sports journalism or real-time expert opinion.

---

### 2.2 Commercial Journalism & Commentary Sources (Withheld / Restricted)

#### Source 3: ESPNcricinfo (Withheld — Commercial Journalism & Editorial Columns)
- **Provider & Canonical URL**: ESPN Inc. / The Walt Disney Company (`https://www.espncricinfo.com/`)
- **Content Type**: Contemporary sports journalism, post-match reports, tactical analysis, match commentary.
- **License / Permission Basis**: **All Rights Reserved (Proprietary)**.
- **Terms of Use & Robots Directives**:
  - `robots.txt` explicitly disallows automated indexing of `/rss/`, `/ci/content/story/`, and live match feeds.
  - Disney Terms of Use Section 3 strictly prohibits data mining, scraping, or automated extraction without express written agreement.
- **Permitted Acquisition Method**: **NONE**.
- **Permissions Audit**:
  - Full-Text Storage: **PROHIBITED**
  - Vector Embedding: **PROHIBITED**
  - Redistribution: **PROHIBITED**
- **Legal Classification**: `REQUIRES_PERMISSION` / `RESTRICTED`.
- **Date & Method of Verification**: 2026-10-24; Inspected `https://www.espncricinfo.com/robots.txt` and Terms of Use.
- **Research Impact**: Crucial news articles cannot be crawled. Stored commentary remains at 0 entries to uphold this boundary.

#### Source 4: Cricbuzz (Withheld — Ball-by-Ball Live Commentary)
- **Provider & Canonical URL**: Cricbuzz.com (Times Internet) (`https://www.cricbuzz.com/`)
- **Content Type**: Proprietary ball-by-ball text commentary, real-time ball descriptions, player quotes.
- **License / Permission Basis**: **All Rights Reserved (Proprietary)**.
- **Terms of Use & Robots Directives**: Terms of Use declare live commentary proprietary intellectual property. Automated scraping is actively detected and blocked.
- **Permitted Acquisition Method**: **NONE** (Bilateral commercial syndication license required).
- **Legal Classification**: `REQUIRES_PERMISSION` / `RESTRICTED`.
- **Date & Method of Verification**: 2026-10-24.
- **Research Impact**: The absence of ball-by-ball commentary prevents cross-source narrative-to-ball alignment. Rather than scraping illegally, Phase 8 and Phase 9 explicitly report `NOT_EVALUABLE` for commentary alignment.

#### Source 5: Wisden (Withheld — Tactical Essays & Magazine Journalism)
- **Provider & Canonical URL**: Wisden Cricket (`https://www.wisden.com/`)
- **Content Type**: In-depth analytical essays, historical rankings, match reports.
- **License / Permission Basis**: **All Rights Reserved (Proprietary)**.
- **Terms of Use & Robots Directives**: Protected by Cloudflare bot protection (HTTP 403/520 on automated requests). Evasion prohibited.
- **Legal Classification**: `REQUIRES_PERMISSION` / `RESTRICTED`.
- **Date & Method of Verification**: 2026-10-24.

---

### 2.3 Proposed Eligible Sources for Research Corpus Expansion

To transition the platform beyond purely encyclopedic Wikipedia articles without violating copyright, candidate open sources were vetted:

#### Candidate 1: Wikinews (Permissively Licensed Journalism)
- **Provider & Canonical URL**: Wikimedia Foundation (`https://en.wikinews.org/`)
- **Content Type**: Contemporary news journalism, match reports written under journalistic style.
- **License / Permission Basis**: **Creative Commons Attribution 2.5 Generic (CC BY 2.5)**.
- **Terms of Use & Robots Directives**: Accessible via MediaWiki REST API (`/api/rest_v1/page/html/`).
- **Permitted Acquisition Method**: Automated API retrieval with rate-limiting ($\le 1.0$ RPS) and standard User-Agent.
- **Attribution Requirements**: Article title, URL, author list, revision ID, CC BY 2.5 notice.
- **Permissions Audit**:
  - Full-Text Storage: **PERMITTED**
  - Vector Embedding: **PERMITTED**
  - Redistribution: **PERMITTED under CC BY 2.5**
- **Suitability Assessment**: High legal suitability. However, Wikinews cricket coverage of the 2024 Men's T20 World Cup is sparse (only 2 volunteer-written tournament articles exist).

#### Candidate 2: BBC Sport Cricket Public RSS (Metadata & Syndicated Excerpts Only)
- **Provider & Canonical URL**: British Broadcasting Corporation (`https://feeds.bbci.co.uk/sport/cricket/rss.xml`)
- **Content Type**: News headlines, 2-sentence syndicated lead paragraphs, publication timestamps, match tags.
- **License / Permission Basis**: **BBC Terms of Use for RSS Feeds** (Personal & Non-commercial research evaluation).
- **Terms of Use & Robots Directives**: RSS feed URL is explicitly public and permitted for automated reading. `robots.txt` permits crawling feed XML.
- **Permitted Acquisition Method**: Standard HTTP `GET` of the XML feed ($\le 1.0$ RPS).
- **Attribution Requirements**: Maintain BBC link and attribution to BBC Sport.
- **Permissions Audit**:
  - Feed Metadata (Title, Date, Link, Summary Excerpt): **PERMITTED**
  - Full-Text Article Body Crawling: **PROHIBITED** (BBC terms disallow scraping full articles at `bbc.com/sport/cricket/`).
- **Legal Classification**: `PERMITTED_METADATA_ONLY`.

#### Candidate 3: The Guardian Open Platform Content API (Developer Research Tier)
- **Provider & Canonical URL**: Guardian News & Media Ltd (`https://open-platform.theguardian.com/`)
- **Content Type**: Contemporary professional cricket journalism, match reports, columnists (e.g., Ali Martin, Andy Bull).
- **License / Permission Basis**: **The Guardian Open Platform Terms & Conditions (Developer Tier)**.
- **Permitted Acquisition Method**: Official REST API query with Developer API Key (`/search?tag=sport/cricket`).
- **Attribution Requirements**: "Powered by Guardian News & Media", canonical link back to Guardian article.
- **Permissions Audit**:
  - Headline, Standfirst & Metadata: **PERMITTED**
  - Full Body Text: **PERMITTED for internal indexing/text-mining** under Developer Tier; caching full text locally for research analysis is authorized, but raw full-text redistribution is prohibited without commercial tier.
- **Legal Classification**: `APPROVED_WITH_API_KEY`. Requires user-supplied API key; no scraping needed.

#### Candidate 4: Open Academic Cricket Datasets (Zenodo / Figshare / Harvard Dataverse)
- **Provider & Canonical URL**: Zenodo (`https://zenodo.org/`), Figshare (`https://figshare.com/`)
- **Content Type**: Pre-compiled research corpora of cricket NLP texts, tournament social commentary, and match statistics.
- **License / Permission Basis**: **Creative Commons Attribution 4.0 (CC BY 4.0)** or **CC0 (Public Domain)**.
- **Permitted Acquisition Method**: Direct DOI archive download.
- **Permissions Audit**: Storage, embeddings, and redistribution fully permitted with citation.
- **Legal Classification**: `APPROVED_OPEN_RESEARCH`.

---

## 3. Comparative Source Governance Summary

| Source Name | Provider | Primary Content Type | License / Basis | Legal Status | Full Text Storage? | Embedding Vectors? | Match-Level Linking? |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **Cricsheet** | Cricsheet.org | Ball-by-ball structured data | ODC-By 1.0 | **APPROVED (Tier A)** | YES | N/A | YES (Deterministic) |
| **Wikipedia** | Wikimedia | Reference, overviews, squads | CC BY-SA 4.0 | **APPROVED (Tier B)** | YES | YES | Bounded (1 Final match, 4 Tournament) |
| **Wikinews** | Wikimedia | Contemporary open journalism | CC BY 2.5 | **APPROVED (Tier B)** | YES | YES | Supported where match-specific |
| **The Guardian API** | Guardian Media | Professional news & analysis | Open Platform Dev | **REQUIRES_API_KEY** | Authorized in cache | YES | YES (Match report tag) |
| **BBC Sport RSS** | BBC | News headlines & lead summaries | BBC RSS Terms | **METADATA_ONLY** | Summaries only | Headings only | YES |
| **ESPNcricinfo** | Disney / ESPN | News, analysis, commentary | All Rights Reserved | **RESTRICTED / WITHHELD** | NO | NO | NO |
| **Cricbuzz** | Times Internet | Ball-by-ball text commentary | All Rights Reserved | **RESTRICTED / WITHHELD** | NO | NO | NO |
| **Wisden** | Wisden | In-depth essays & ratings | Cloudflare Edge / ARR | **RESTRICTED / WITHHELD** | NO | NO | NO |

---

## 4. Policy Protocol for Phase 9 and Beyond

1. **Strict Rejection of Evasion**: Any pull request or script containing Cloudflare bypass logic, rotating proxies for scraping, or fake User-Agent impersonation will be rejected immediately.
2. **Provenance Mandatory on Ingestion**: Ingested records must store `source_record_id`, `canonical_url`, `content_hash_sha256`, `license_tag`, `attribution_text`, `retrieval_timestamp_utc`, and `publication_timestamp_utc`.
3. **Explicit Handling of Absent Data**: When legal access to live commentary or proprietary journalism is unavailable, the system will explicitly report `INSUFFICIENT_DATA` or `NOT_EVALUABLE` rather than fabricating synthetic data or scraping prohibited endpoints.
