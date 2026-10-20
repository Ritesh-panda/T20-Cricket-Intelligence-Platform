# Source Configuration & Registry Guide

## 1. Configuration-Driven Architecture

Data acquisition in the T20 Cricket Intelligence Platform is strictly driven by configuration declared in `config/sources.yaml`. No individual publisher access logic, domain hardcoding, or arbitrary throttling rules exist within the core scheduler or adapters.

Each source profile defines:
- A stable source identifier.
- Source category (`structured_data`, `commentary`, `news`, `rss`, `sitemap`, `api`).
- Base URL and permitted discovery endpoints.
- Adapter binding (`cricsheet`, `commentary`, `news`).
- Enablement state (`enabled: true/false`).
- Ethical rate limiting (`rate_limit_rps`) and timeouts (`request_timeout_sec`).
- Bounded retries (`max_retries`) and response size limit (`max_response_bytes`).
- Supported MIME content types (`supported_content_types`).
- Collection & data retention constraints (`retention_policy`).
- Licensing audit tags (`license_tag`) and legal compliance notes (`licence_notes`).
- Domain allowlist for redirect boundary enforcement (`allowed_domains`).

---

## 2. Source Configuration Schema

The YAML configuration maps directly to the strongly-typed `SourceConfig` Pydantic model in [`src/pipeline/config.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/pipeline/config.py):

```yaml
sources:
  <source_id>:
    source_id: str                      # Stable identifier (e.g. cricsheet, espncricinfo)
    name: str                           # Descriptive human name
    category: str                       # structured_data | commentary | news | rss | sitemap | api
    base_url: str                       # Root URL or archive download base
    discovery_endpoints:                # Permitted RSS, sitemap, or index URLs
      - str
    adapter_id: str                     # Target adapter: cricsheet | commentary | news
    enabled: bool                       # Active crawl enablement flag
    rate_limit_rps: float               # Maximum requests per second (<= 0.5 for web crawling)
    request_timeout_sec: int            # Read/connect timeout (typically 15-30s)
    max_retries: int                    # Maximum exponential backoff retry attempts (typically 3)
    max_response_bytes: int             # Maximum allowed payload size in bytes (e.g. 10485760 for 10MB)
    supported_content_types:            # Permitted MIME types
      - str
    retention_policy:
      store_full_text: bool             # Whether raw journalistic body text can legally be stored
      store_summary_only: bool          # Whether only extractive summary/metadata is retained
      redistributable: bool             # Whether raw records may be redistributed publicly
      retention_days: int | null        # Bounded retention lifecycle if applicable
    license_tag: str                    # Declared license e.g. ODbL-1.0, FairUse-ResearchExtraction
    licence_notes: str                  # Specific terms and attribution requirements
    allowed_domains:                    # Allowed netlocs for crawling and redirect boundaries
      - str
    custom_metadata:                    # Source-specific configuration dictionary
      key: value
```

---

## 3. Registered Source Profiles

| Source ID | Name | Category | Adapter | Rate Limit | License | Retention Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`cricsheet`** | Cricsheet T20 Open Data | `structured_data` | `cricsheet` | `0.0 RPS` (local/batch) | `ODbL-1.0` | Full retention & redistributable. Attribution required. |
| **`espncricinfo`** | ESPNcricinfo News & Reviews | `news` | `news` | `0.5 RPS` (1 req / 2s) | `FairUse-ResearchExtraction` | Summary & metadata only. Full text not redistributable. |
| **`cricbuzz`** | Cricbuzz Commentary | `commentary` | `commentary` | `0.33 RPS` (1 req / 3s) | `FairUse-ResearchExtraction` | Factual ball-by-ball commentary text and milestone tags. |
| **`wisden`** | Wisden Editorial & Analysis | `news` | `news` | `0.5 RPS` (1 req / 2s) | `FairUse-ResearchExtraction` | Summary & metadata only. Full text not redistributable. |

---

## 4. Enabling & Modifying Sources

### Step 1: Review Publisher Access & Robots Directives
Before setting `enabled: true` for any new source:
1. Inspect the domain's `robots.txt` (e.g., `https://example.com/robots.txt`).
2. Identify permitted paths and rate-limit directives (e.g., `Crawl-delay`).
3. Ensure the access method uses public RSS/Atom feeds, public sitemaps, or authorized open data downloads.
4. Verify that no authentication, paywalls, CAPTCHAs, or anti-bot evasions are required.

### Step 2: Declare Retention Constraints
If the source produces copyrighted journalistic prose (e.g., editorial commentary, long-form journalism):
- Set `store_full_text: false`.
- Set `store_summary_only: true`.
- Set `redistributable: false`.
- Set `license_tag: FairUse-ResearchExtraction`.

### Step 3: Validate Configuration via CLI
Verify the configuration with the CLI:
```bash
python -m src.pipeline list
```
Execute a dry run to verify parsing and validation before persistent storage:
```bash
python -m src.pipeline run --source <source_id> --dry-run --limit 3
```
