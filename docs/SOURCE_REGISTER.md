# Source Register & Provenance Ledger: T20 Cricket Intelligence Platform

## 1. Primary External Data Sources & Legal Compliance Matrix

| Source Name | Primary Data Type | Official Source URL / Dataset Ref | Acquisition Mechanism | License / Terms Reference | Permitted Storage & Scope | Rate Limits / Policy | Last Checked | Operational Status & Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cricsheet** | Ball-by-ball structured match deliveries, scorecards, registries | `https://cricsheet.org/downloads/t20s_male_json.zip` | Bulk direct download (JSON v1.2.0) | Open Data Commons Attribution License (ODC-By 1.0) | Full structured scorecards, ball-by-ball facts, and canonical entities. Redistributable with attribution. | N/A (Static archive caching) | 2026-10-24 | **Approved & Ingested (Tier A)**: 10 matches (2,314 deliveries) from ICC Men's T20 World Cup 2024. |
| **Wikimedia / Wikipedia** | Match reports, tournament overviews, squad registries, historical analysis | `https://en.wikipedia.org/api/rest_v1/page/html/` | Official REST API | Creative Commons Attribution-ShareAlike 4.0 (CC-BY-SA 4.0) | Full text, segmented paragraphs, extractive summaries. Full attribution and license tracking. | 1.0 RPS (polite header `T20CricketResearchBot/1.0`) | 2026-10-24 | **Approved & Ingested (Tier B)**: 5 comprehensive tournament articles (314 paragraphs). |
| **ESPNcricinfo** | News journalism, post-match analysis, editorial columns | `https://www.espncricinfo.com` | Web crawling / RSS feeds | Website Terms of Use & `robots.txt` (`Disallow: /rss/`) | **Restricted**: Automated crawling disallowed by `robots.txt`. Full text retention prohibited without explicit bilateral license. | Max 0.5 RPS (if authorized) | 2026-10-24 | **Withheld (Ethics Constraint)**: Excluded in Phase 7 to respect publisher `robots.txt`. Do not bypass anti-crawler directives. |
| **Cricbuzz** | Ball-by-ball commentary, live text streams | `https://www.cricbuzz.com` | Web streams / API endpoints | Website Terms of Use & IP Protection | **Restricted**: Live ball-by-ball commentary is proprietary commercial content. Commercial redistribution prohibited. | Max 0.33 RPS | 2026-10-24 | **Withheld (Tier C Limitation)**: Automated commercial scraping withheld. Documented as a research limitation. |
| **Wisden** | Tactical essays, historical commentary, player ratings | `https://www.wisden.com` | Web crawling | Website Terms & Cloudflare Edge Protection | **Restricted**: Web edge challenges automated requests (HTTP 520). Reverse engineering or proxy evasion strictly prohibited. | Max 0.5 RPS | 2026-10-24 | **Withheld**: Evasion of Cloudflare challenges is unethical and prohibited. |
| **BBC Sport Cricket** | News headlines, syndicate summaries | `https://feeds.bbci.co.uk/sport/cricket/rss.xml` | Public RSS syndication | BBC Terms of Use (`robots.txt` permits crawling of feeds) | Metadata, article titles, summary excerpts, and canonical URLs only. No bulk full-text reproduction. | 1.0 RPS | 2026-10-24 | **Verified & Permitted**: Suitable for real-time headline syndication; historical match archive maintained via CC-BY-SA. |

---

## 2. Ingested Real-World Corpus Provenance Ledger (Phase 7)

### Tier A: Structured Cricsheet Matches (ICC Men's T20 World Cup 2024)

| File / Source ID | Match ID | Match Date | Teams | Winner | Deliveries | Ingested SHA-256 | License |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `1415701.json` | `cric_20240601_can_uni` | 2024-06-01 | Canada vs USA | United States | 241 | `856b559017ff...` | ODC-By 1.0 |
| `1415711.json` | `cric_20240606_pak_uni` | 2024-06-06 | Pakistan vs USA | United States (Super Over) | 270 | `9be1f17a9836...` | ODC-By 1.0 |
| `1415719.json` | `cric_20240609_ind_pak` | 2024-06-09 | India vs Pakistan | India (6 runs) | 243 | `2d8977a5e9f1...` | ODC-By 1.0 |
| `1415742.json` | `cric_20240619_wes_eng` | 2024-06-19 | West Indies vs England | England (8 wkts) | 241 | `f77916db6ca8...` | ODC-By 1.0 |
| `1415744.json` | `cric_20240620_ban_aus` | 2024-06-20 | Bangladesh vs Australia | Australia (DLS) | 195 | `270928b52f6b...` | ODC-By 1.0 |
| `1415749.json` | `cric_20240623_uni_eng` | 2024-06-23 | USA vs England | England (10 wkts) | 177 | `266395b29dbf...` | ODC-By 1.0 |
| `1415750.json` | `cric_20240623_wes_sou` | 2024-06-23 | West Indies vs South Africa | South Africa (DLS) | 230 | `87b649eead90...` | ODC-By 1.0 |
| `1415751.json` | `cric_20240624_ind_aus` | 2024-06-24 | India vs Australia | India (24 runs) | 245 | `264b3f81e35d...` | ODC-By 1.0 |
| `1415754.json` | `cric_20240627_ind_eng` | 2024-06-27 | India vs England (SF2) | India (68 runs) | 221 | `30a6cba2fa8d...` | ODC-By 1.0 |
| `1415755.json` | `cric_20240629_ind_sou` | 2024-06-29 | India vs South Africa (Final) | India (7 runs, Champions) | 251 | `0bc78686bfbb...` | ODC-By 1.0 |

### Tier B: Editorial Journalism & Tournament Reports (Wikimedia CC-BY-SA 4.0)

| Document Identifier | Document Title | Publication Date | Paragraphs | Word Count | Canonical URL | Linked Match | Ingested SHA-256 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `2024_Men's_T20_World_Cup_final.html` | 2024 Men's T20 World Cup Final: India vs South Africa | 2024-06-29 | 36 | 1,480 | `https://en.wikipedia.org/wiki/2024_Men%27s_T20_World_Cup_final` | `cric_20240629_ind_sou` (Conf: 1.00) | `16d1c4c64576...` |
| `2024_Men's_T20_World_Cup.html` | 2024 ICC Men's T20 World Cup Tournament Overview | 2024-06-30 | 104 | 4,210 | `https://en.wikipedia.org/wiki/2024_Men%27s_T20_World_Cup` | Unresolved (Ambiguous tournament-wide coverage) | `e281edc5bf0ad...` |
| `India_at_the_Men's_T20_World_Cup.html` | India Campaign and History at the Men's T20 World Cup | 2024-06-30 | 58 | 2,130 | `https://en.wikipedia.org/wiki/India_at_the_Men%27s_T20_World_Cup` | Unresolved (Multi-match coverage) | `d5df20f39a3b...` |
| `2024_Men's_T20_World_Cup_squads.html` | 2024 Men's T20 World Cup Official Squads | 2024-06-01 | 72 | 3,890 | `https://en.wikipedia.org/wiki/2024_Men%27s_T20_World_Cup_squads` | `cric_20240601_can_uni` (Conf: 0.95) | `345d60cf455b...` |
| `India-Pakistan_cricket_rivalry.html` | India vs Pakistan Cricket Rivalry & T20 Clashes | 2024-06-09 | 44 | 1,940 | `https://en.wikipedia.org/wiki/India%E2%80%93Pakistan_cricket_rivalry` | `cric_20240609_ind_pak` (Conf: 0.90) | `aff0d530c704...` |

---

## 3. Upstream Open-Source Repositories Ledger

| # | Repository Name | Upstream URL | Target Commit Hash | License | Evaluated Modules | Reuse Decision | Attribution / Legal Notice | Integration Status |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **ZainZoy/NLP-project** | `https://github.com/ZainZoy/NLP-project` | `76578b4678` | None | Commentary parser, score validation gate | **ADAPT** | "Adapted from commentary parsing concepts by ZainZoy" | Integrated in `CommentaryAdapter` |
| 2 | **princyhareshbhai1530/T20-Commentary-Analysis** | `https://github.com/princyhareshbhai1530/T20-Commentary-Analysis` | `af64837c57` | None | Excitement keywords, phase definitions | **REFERENCE ONLY** | Domain keyword reference only; no code incorporated | Reference Logged |
| 3 | **HalcyonVector/Cricket-Intelligence-Lab** | `https://github.com/HalcyonVector/Cricket-Intelligence-Lab` | `57be3daf1f` | None | Next.js JSON extractor, Cricsheet parser | **ADAPT** | "Adapted from Cricbuzz extraction heuristic by HalcyonVector" | Integrated in adapters |
| 4 | **vinaybale-collab/cricket-analytics-web** | `https://github.com/vinaybale-collab/cricket-analytics-web` | `4cffafabdf` | None | DuckDB analytics, dashboard architecture | **REFERENCE ONLY** | Architecture and query patterns referenced; no code copied | Reference Logged |
| 5 | **Anurag9557/cricket-iq** | `https://github.com/Anurag9557/cricket-iq` | `8c67a120b8` | **MIT License** | Chase-state builder, win probability | **REUSE / ADAPT** | **Full MIT Copyright Notice required**: "Copyright (c) 2026 ANURAG PRAKASH" | Ready for Polars Integration |
| 6 | **ShrinathSontakke/Cricket-Data-Analytics** | `https://github.com/ShrinathSontakke/Cricket-Data-Analytics` | `1448b257bc` | None | PowerBI reports, paid scraper scripts | **REJECT** | None (Code rejected) | Rejected |
| 7 | **Paul-ans-typ/Analysis-of-Cricket-Commentary** | `https://github.com/Paul-ans-typ/Analysis-of-Cricket-Commentary` | `e580d8faa0` | None | RNN commentary score prediction | **REJECT** | None (Code rejected) | Rejected |
| 8 | **sst-cloud-solutions/h25-sports** | `https://github.com/sst-cloud-solutions/h25-sports` | `47bbce7622` | **UNLICENSED (Private)** | NestJS backend, Next.js frontend | **REJECT** | **Legal prohibition on code reuse** (Declared UNLICENSED) | Rejected |
| 9 | **SRIHARI18V/CRICKET-RAG-CHATBOT** | `https://github.com/SRIHARI18V/CRICKET-RAG-CHATBOT` | `f94d1b9668` | None | Hybrid query router (stats vs RAG) | **REFERENCE ONLY** | Architectural router pattern referenced; no code copied | Reference Logged |
