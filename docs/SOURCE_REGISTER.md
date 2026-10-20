# Source Register & Provenance Ledger: T20 Cricket Intelligence Platform

## 1. Data Source Inventory & Legal Assessment

Before creating any adapter, every external publisher or open data source must be formally vetted across legal, licensing, technical, and structural dimensions.

| Source Name | Primary Data Type | Permitted Access Method | Terms / Licensing Notes | Rate Limit Policy | Operational Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cricsheet** | Ball-by-ball structured match deliveries, scorecards | Bulk direct download (YAML / JSON / CSV) | Open Data under Open Database License (ODbL) / Creative Commons Attribution (CC-BY). Commercial and research use permitted with attribution. | N/A (Static file download / caching) | **Approved & Priority 1** (Core match ground truth) |
| **ESPNcricinfo** | News articles, post-match analysis, editorial pieces, commentary | Web crawling of public article pages via sitemaps / RSS feeds | Strict adherence to `robots.txt`. Commercial redistribution of raw articles prohibited. Research extraction of text for embedding and analysis under Fair Use principles; no scraping of paywalled or subscriber content. | Max 0.5 requests/sec, burst 1, exponential backoff | **Pending Adapter Implementation** (Adheres to polite headers and robots.txt) |
| **Cricbuzz** | Match previews, commentary, news updates | Public article crawling and live text commentary feeds | Inspect `robots.txt`. Do not bypass anti-bot shields or reverse-engineer private/app APIs. Text extracted must remain local for indexing and derivative embedding. | Max 0.33 requests/sec (1 req / 3 sec) | **Pending Adapter Implementation** |
| **Wisden** | Tactical long-form essays, historical commentary, player ratings | Public editorial article crawling via sitemap | Standard website terms; no unauthorized bulk scraping of entire archives. Respect crawl-delay and disallow rules. | Max 0.5 requests/sec | **Pending Adapter Implementation** |
| **ICC Official** | Official tournament schedules, squad announcements, match summaries | Official tournament website public media releases | Verify `robots.txt`. Extract only public tournament press releases and official squad lists. | Max 0.5 requests/sec | **Evaluation Mode** |

---

## 2. Upstream Open-Source Repositories Ledger

*Note: Repositories will be populated once the curated repository URL list is provided. All clones are quarantined under `research_sources/` (git-ignored).*

| Repository Name | Upstream URL | Target Commit Hash | License | Evaluated Modules | Reuse Decision | Attribution / Legal Notice | Integration Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| *TBD (Batch 1)* | *Awaiting input* | *TBD* | *TBD* | *Scrapers / Adapters* | *Pending Audit* | *TBD* | Unaudited |
| *TBD (Batch 2)* | *Awaiting input* | *TBD* | *TBD* | *Commentary NLP* | *Pending Audit* | *TBD* | Unaudited |
| *TBD (Batch 3)* | *Awaiting input* | *TBD* | *TBD* | *Match Analytics* | *Pending Audit* | *TBD* | Unaudited |
| *TBD (Batch 4)* | *Awaiting input* | *TBD* | *TBD* | *Clustering / Viz* | *Pending Audit* | *TBD* | Unaudited |

### Decision Taxonomy
- **REUSE**: Code is clean, well-tested, actively maintained, has a compatible permissive license (MIT, Apache 2.0, BSD), and directly addresses a required module interface with minimal modifications.
- **ADAPT**: Algorithmic logic or parsing heuristic is valuable but tightly coupled to obsolete libraries or idiosyncratic schemas. The logic will be refactored to fit our canonical Pydantic schemas.
- **REFERENCE ONLY**: Architectural concept, gazetteer list, or research paper implementation that provides conceptual guidance, but code itself will not be copied or directly depended upon.
- **REJECT**: Deprecated, unmaintained, security vulnerabilities, incompatible copyleft license (e.g. AGPL without isolation plan), bypasses paywalls/security, or introduces bloated dependencies.

---

## 3. Provenance Tracking Schema

Every record in the storage layer tracks provenance through this structure:

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
