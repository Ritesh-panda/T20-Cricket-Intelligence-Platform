# Source Register & Provenance Ledger: T20 Cricket Intelligence Platform

## 1. Primary External Data Sources

| Source Name | Primary Data Type | Permitted Access Method | Terms / Licensing Notes | Rate Limit Policy | Operational Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cricsheet** | Ball-by-ball structured match deliveries, scorecards, registries | Bulk direct download (YAML / JSON / CSV) | Open Data under Open Database License (ODbL) / Creative Commons Attribution (CC-BY). Commercial and research use permitted with attribution. | N/A (Static file download / caching) | **Approved & Priority 1** (Core match ground truth) |
| **ESPNcricinfo** | News articles, post-match analysis, editorial pieces, commentary | Web crawling of public article pages via sitemaps / RSS feeds | Strict adherence to `robots.txt`. Commercial redistribution of raw articles prohibited. Research extraction of text for embedding and analysis under Fair Use principles; no scraping of paywalled or subscriber content. | Max 0.5 requests/sec, burst 1, exponential backoff | **Approved via Trafilatura Adapter** |
| **Cricbuzz** | Match previews, commentary, live text feeds | Public page extraction via Next.js streaming JSON payloads (`self.__next_f`) | Inlines clean structured JSON in public HTML without requiring browser automation or API keys. Must respect rate limits and keep text local. | Max 0.33 requests/sec (1 req / 3 sec) | **Approved via Lightweight JSON Adapter** |
| **Wisden** | Tactical long-form essays, historical commentary, player ratings | Public editorial article crawling via sitemap | Standard website terms; no unauthorized bulk scraping of entire archives. Respect crawl-delay and disallow rules. | Max 0.5 requests/sec | **Approved via Trafilatura Adapter** |
| **ICC Official** | Official tournament schedules, squad announcements, match summaries | Official tournament website public media releases | Verify `robots.txt`. Extract only public tournament press releases and official squad lists. | Max 0.5 requests/sec | **Approved for Gazetteer Squad Lists** |

---

## 2. Upstream Open-Source Repositories Ledger

All upstream candidate repositories have been cloned into the quarantined directory `research_sources/` (git-ignored) and formally evaluated.

| # | Repository Name | Upstream URL | Target Commit Hash | License | Evaluated Modules | Reuse Decision | Attribution / Legal Notice | Integration Status |
| :-: | :--- | :--- | :--- | :--- | :--- | :---: | :--- | :---: |
| 1 | **ZainZoy/NLP-project** | `https://github.com/ZainZoy/NLP-project` | `76578b46787acf6408d64b0d49c233e27de029c0` | Missing (None) | Commentary parser, score validation gate, turning point detector | **ADAPT** | "Adapted from commentary parsing concepts by ZainZoy" | Ready for Schema Adaptation |
| 2 | **princyhareshbhai1530/T20-Commentary-Analysis** | `https://github.com/princyhareshbhai1530/T20-Commentary-Analysis` | `af64837c57b3163c2e181e76cf4b82683f17cc83` | Mentioned MIT in README, no file | Excitement score keywords, phase definition | **REFERENCE ONLY** | Domain keyword reference only; no code incorporated | Concept Logged |
| 3 | **HalcyonVector/Cricket-Intelligence-Lab** | `https://github.com/HalcyonVector/Cricket-Intelligence-Lab` | `57be3daf1f92bdcca55eb8ce95fbcd1c1a3409f9` | None (ODbL / CC BY-SA for data) | Cricbuzz Next.js JSON extractor, Cricsheet `orjson` parser | **ADAPT** | "Adapted from Cricbuzz extraction heuristic by HalcyonVector" | Ready for Adapter Integration |
| 4 | **vinaybale-collab/cricket-analytics-web** | `https://github.com/vinaybale-collab/cricket-analytics-web` | `4cffafabdf0eef30db05cc6c41134221f26f2d97` | None (CC BY 4.0 for data) | DuckDB SQL analytics, Next.js dashboard UI | **REFERENCE ONLY** | Architecture and query patterns referenced; no code copied | Concept Logged |
| 5 | **Anurag9557/cricket-iq** | `https://github.com/Anurag9557/cricket-iq` | `8c67a120b85ada7855bfaeaa161951277ded1781` | **MIT License** | Polars chase-state builder, win probability calibration, verification gate | **REUSE / ADAPT** | **Full MIT Copyright Notice required**: "Copyright (c) 2026 ANURAG PRAKASH" | Ready for Polars Integration |
| 6 | **ShrinathSontakke/Cricket-Data-Analytics** | `https://github.com/ShrinathSontakke/Cricket-Data-Analytics` | `1448b257bc935541b8d48edfdcb5b17ea7171d02` | None | PowerBI reports, paid scraper scripts | **REJECT** | None (Code rejected) | Rejected |
| 7 | **Paul-ans-typ/Analysis-of-Cricket-Commentary** | `https://github.com/Paul-ans-typ/Analysis-of-Cricket-Commentary` | `e580d8faa0d37b463ab26677d22aded5e4099d77` | None | RNN commentary score prediction | **REJECT** | None (Code rejected) | Rejected |
| 8 | **sst-cloud-solutions/h25-sports** | `https://github.com/sst-cloud-solutions/h25-sports` | `47bbce76226603aa1b6a6b4bf9fa21241338d6a3` | **UNLICENSED (Private)** | NestJS backend, Next.js frontend, mock data | **REJECT** | **Legal prohibition on code reuse** (Declared UNLICENSED) | Rejected |
| 9 | **SRIHARI18V/CRICKET-RAG-CHATBOT** | `https://github.com/SRIHARI18V/CRICKET-RAG-CHATBOT` | `f94d1b9668c8ca47ecb484c7ad5d03635b74f1ae` | None | Hybrid query router (stats vs RAG) | **REFERENCE ONLY** | Architectural router pattern referenced; no code copied | Concept Logged |

---

## 3. Provenance Tracking Record Format

Every raw payload and parsed record ingested into `data/raw/` and `data/processed/` records provenance matching the following structure:

```json
{
  "provenance_id": "prov_7f8c9b2a1e",
  "source_name": "cricsheet",
  "source_identifier": "1411166.json",
  "source_url": "https://cricsheet.org/downloads/t20s_json.zip",
  "harvest_timestamp_utc": "2026-10-20T14:30:00Z",
  "http_status": 200,
  "content_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "pipeline_version": "1.0.0",
  "license_tag": "ODbL-1.0",
  "redistributable": false
}
```
