# Source Register & Provenance Ledger: T20 Cricket Intelligence Platform

## 1. Primary External Data Sources & Legal Compliance Matrix

| Source Name | Primary Data Type | Official Source URL / Dataset Ref | Acquisition Mechanism | License / Terms Reference | Permitted Storage & Scope | Rate Limits / Policy | Last Checked | Operational Status & Legal Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cricsheet** | Ball-by-ball structured match deliveries, scorecards, registries | `https://cricsheet.org/downloads/t20s_male_json.zip` | Bulk direct download (JSON v1.2.0) | Open Data Commons Attribution License (ODC-By 1.0) / CC BY 4.0 | Full structured scorecards, ball-by-ball facts, and canonical entities. Redistributable with attribution. | N/A (Static archive caching) | 2026-10-24 | **Approved & Ingested (Tier A)**: 10 matches (2,314 deliveries) from ICC Men's T20 World Cup 2024. |
| **Wikimedia / Wikipedia** | Match reports, tournament overviews, squad registries, historical analysis | `https://en.wikipedia.org/api/rest_v1/page/html/` | Official REST API | Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0) | Full text, segmented paragraphs, extractive summaries. Full attribution and license tracking. | 1.0 RPS (polite header `T20CricketResearchBot/1.0`) | 2026-10-24 | **Approved & Ingested (Tier B)**: 5 comprehensive tournament articles (314 paragraphs). |
| **Wikinews** | Contemporary open sports journalism and match reports | `https://en.wikinews.org/api/rest_v1/page/html/` | Official REST API | Creative Commons Attribution 2.5 (CC BY 2.5) | Full article prose, lead paragraphs, author metadata. Fully redistributable with attribution. | 1.0 RPS | 2026-10-24 | **Approved (Tier B)**: Eligible for future tournament journalism ingestion. |
| **The Guardian Open Platform** | Professional contemporary cricket journalism & analysis | `https://open-platform.theguardian.com/` | Official REST API with Developer Key | Guardian Open Platform Terms (Developer Tier) | Indexing, entity extraction, sentiment, and dense embeddings permitted. Raw full-text redistribution prohibited. | 1.0 RPS (Developer quota: 500 req/day) | 2026-10-24 | **Approved with API Key**: Eligible when user provides `GUARDIAN_API_KEY`. |
| **BBC Sport Cricket** | News headlines, syndicate summaries | `https://feeds.bbci.co.uk/sport/cricket/rss.xml` | Public RSS syndication | BBC Terms of Use (`robots.txt` permits feed crawling) | Metadata, article titles, summary excerpts, and canonical URLs only. No bulk full-text reproduction. | 1.0 RPS | 2026-10-24 | **Approved for Metadata Only**: Suitable for real-time headline syndication; historical match archive maintained via CC BY-SA. |
| **ESPNcricinfo** | News journalism, post-match analysis, editorial columns | `https://www.espncricinfo.com` | Web crawling / RSS feeds | Website Terms of Use & `robots.txt` (`Disallow: /rss/`) | **Restricted**: Automated crawling disallowed by `robots.txt`. Full text retention prohibited without explicit bilateral license. | Max 0.5 RPS (if authorized) | 2026-10-24 | **Withheld (Ethics Constraint)**: Excluded to respect publisher `robots.txt`. Do not bypass anti-crawler directives. |
| **Cricbuzz** | Ball-by-ball commentary, live text streams | `https://www.cricbuzz.com` | Web streams / API endpoints | Website Terms of Use & IP Protection | **Restricted**: Live ball-by-ball commentary is proprietary commercial content. Commercial redistribution prohibited. | Max 0.33 RPS | 2026-10-24 | **Withheld (Tier C Limitation)**: Automated commercial scraping withheld. Documented as a research limitation. |
| **Wisden** | Tactical essays, historical commentary, player ratings | `https://www.wisden.com` | Web crawling | Website Terms & Cloudflare Edge Protection | **Restricted**: Web edge challenges automated requests (HTTP 520). Reverse engineering or proxy evasion strictly prohibited. | Max 0.5 RPS | 2026-10-24 | **Withheld**: Evasion of Cloudflare challenges is unethical and prohibited. |

---

## 2. Ingested Real-World Corpus Provenance Ledger

### Tier A: Structured Cricsheet Matches (ICC Men's T20 World Cup 2024)

| File / Source ID | Match ID | Match Date | Teams | Winner | Deliveries | Ingested SHA-256 | License |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| `1415701.json` | `cric_20240601_can_uni` | 2024-06-01 | Canada vs USA | United States (7 wkts) | 226 | `856b559017ff782bc30dfeb546fa6840fdb80fc19f8f8d3e1f90bf8faf6c8ad3` | ODC-By 1.0 |
| `1415711.json` | `cric_20240606_pak_uni` | 2024-06-06 | Pakistan vs USA | United States (Super Over) | 270 | `9be1f17a9836211364937d02228a66793edd32e0d27aab5445210b4c479cb694` | ODC-By 1.0 |
| `1415719.json` | `cric_20240609_ind_pak` | 2024-06-09 | India vs Pakistan | India (6 runs) | 239 | `9610b19b945c6437703ce44ec54d00ea7db7e5b770081c70518741d0e473b666` | ODC-By 1.0 |
| `1415742.json` | `cric_20240619_wes_eng` | 2024-06-19 | West Indies vs England | England (8 wkts) | 222 | `c61b8f8c189ccb3505ef62bc5ef1b0e4729b9c49b464b749e8110d49922939a0` | ODC-By 1.0 |
| `1415744.json` | `cric_20240620_ban_aus` | 2024-06-20 | Bangladesh vs Australia | Australia (28 runs DLS) | 126 | `c55ee4c30df25083e7d39e83dbbf78293694d7dbc3ae153eaf7467ff0d9da346` | ODC-By 1.0 |
| `1415749.json` | `cric_20240623_uni_eng` | 2024-06-23 | USA vs England | England (10 wkts) | 179 | `67aaecd87c3ae8da2a8d8b839c658767ec36cce1d8236f998adcd05eafd6c723` | ODC-By 1.0 |
| `1415750.json` | `cric_20240623_wes_sou` | 2024-06-23 | West Indies vs South Africa | South Africa (3 wkts DLS) | 204 | `c38bd22041dc75e3e2b55c8a8bb581768c0a0b1b270b260e7cf0388c99a0e83c` | ODC-By 1.0 |
| `1415751.json` | `cric_20240624_ind_aus` | 2024-06-24 | India vs Australia | India (24 runs) | 246 | `26a2f1005dcdfdcc39e217f6c33dbb7b55e846fb6f417578a5b8225738a3b053` | ODC-By 1.0 |
| `1415754.json` | `cric_20240627_ind_eng` | 2024-06-27 | India vs England (SF2) | India (68 runs) | 237 | `448175687d76966fe1cdda6bcf0f9cf49f59f7f900ef9d82f2348378283f0ebb` | ODC-By 1.0 |
| `1415755.json` | `cric_20240629_ind_sou` | 2024-06-29 | India vs South Africa (Final) | India (7 runs, Champions) | 245 | `0bc78686bf2a6e32a708a829e95d0318d10adda6b7ac88a176de7e8efa41ee35` | ODC-By 1.0 |
| **Totals** | — | — | **10 Matches** | — | **2,314** | — | — |

---

### Tier B: Editorial Journalism & Tournament Reports (Wikimedia CC BY-SA 4.0)

| Document Identifier | Document Title | Revision Timestamp (`dc:modified`) | Retrieval Timestamp | Scope | Linked Match | Ingested SHA-256 | License |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| `2024_Men's_T20_World_Cup_final.html` | 2024 Men's T20 World Cup Final: India vs South Africa | 2026-09-26T10:11:43Z | 2026-10-24T08:00:00Z | `single_match` | `cric_20240629_ind_sou` | `16d1c4c6457636e78ba772921da8a67bf285f5e27a6c9cfd313be2b3cbba216d` | CC BY-SA 4.0 |
| `2024_Men's_T20_World_Cup.html` | 2024 ICC Men's T20 World Cup Tournament Overview | 2026-09-26T10:12:01Z | 2026-10-24T08:00:00Z | `tournament` | `null` (Tournament-wide) | `e281edc5bf0ad6b653f5da19559c5d0705a181180ae14b7e8d53344d9302157a` | CC BY-SA 4.0 |
| `India_at_the_Men's_T20_World_Cup.html` | India Campaign and History at the Men's T20 World Cup | 2026-09-19T05:56:22Z | 2026-10-24T08:00:00Z | `team_campaign` | `null` (Multi-match) | `d5df20f39a3b8364531818d6a8ad5cff9d71c1bb84df7b4cb7df50901e16f396` | CC BY-SA 4.0 |
| `2024_Men's_T20_World_Cup_squads.html` | 2024 Men's T20 World Cup Official Squads | 2026-07-19T20:19:08Z | 2026-10-24T08:00:00Z | `tournament` (rosters) | `null` (Non-match squad list) | `345d60cf455bb3ecdc76891ebfa7859b8be5d7620a811c0dfef462cefc3f9e85` | CC BY-SA 4.0 |
| `India-Pakistan_cricket_rivalry.html` | India vs Pakistan Cricket Rivalry & T20 Clashes | 2026-10-19T07:45:20Z | 2026-10-24T08:00:00Z | `historical_context` | `null` (Historical bilateral) | `aff0d530c704f7c180907d0f912c3f87b8979313ea595d28b16bbab8f62f33f1` | CC BY-SA 4.0 |

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
