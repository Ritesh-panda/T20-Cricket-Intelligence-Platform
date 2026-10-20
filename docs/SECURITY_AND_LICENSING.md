# Security, Compliance & Licensing Policy

## 1. Compliance Philosophy & Legal Boundaries

The T20 Cricket Intelligence Platform operates strictly within legal, copyright, and ethical research boundaries:

1. **No Paywall or Security Bypass**:
   The system shall NEVER attempt to bypass paywalls, solve CAPTCHAs, spoof session cookies, or access restricted subscriber content.
2. **Strict Adherence to `robots.txt`**:
   Before initiating crawling on any domain, the ingestion engine queries and parses `robots.txt`. Any URI path matched by a `Disallow` directive is strictly excluded from collection.
3. **Transparent Identification**:
   All automated network requests MUST supply a transparent, responsible HTTP `User-Agent` header containing project identity and contact details:
   ```http
   User-Agent: T20CricketResearchBot/1.0 (+https://github.com/example/t20-cricket-intel; contact@research.example.org)
   ```
4. **Polite Crawling & Concurrency Controls**:
   Maximum crawling frequency is capped at 0.5 requests per second (1 request every 2 seconds) per domain, with exponential backoff on HTTP 429 (Too Many Requests) or HTTP 5xx responses.

---

## 2. Intellectual Property & Redistribution Rules

### 2.1 Raw Journalism & Editorial Content
- News articles and commentary published by third parties (e.g., ESPNcricinfo, Cricbuzz, Wisden) are protected by copyright.
- **Fair Use for Computational Research**: Collecting and processing articles for non-commercial academic research, topic modeling, named entity recognition, and semantic analysis qualifies as transformative fair use.
- **Redistribution Prohibition**: Raw article bodies and verbatim full texts MUST NOT be redistributed publicly in GitHub repositories or open data dumps.
- **Permitted Public Derivatives**: Extracted metadata (headline, publication date, URL), computed topic cluster labels, entity mention counts, sentiment scores, and mathematical embeddings (vector arrays) may be redistributed as non-copyright-infringing analytical derivatives.

### 2.2 Open Match Datasets (Cricsheet)
- Cricsheet data is licensed under the **Open Database License (ODbL)** and/or Creative Commons Attribution (CC-BY 4.0).
- Users may freely share, modify, and build upon the data, provided that attribution to Cricsheet is clearly maintained in the UI, documentation, and metadata exports.

---

## 3. Upstream Open-Source Licensing Compatibility

All candidate repositories and external dependencies must comply with the platform's licensing matrix:

| License Type | Permitted in Core Pipeline? | Conditions / Handling Requirements |
| :--- | :---: | :--- |
| **MIT / BSD / ISC** | **YES** | Retain original copyright notices and license text in `LICENSES.md`. |
| **Apache 2.0** | **YES** | Retain copyright notice, license text, and document any modifications in state changes. |
| **GPL v2 / v3** | **CONDITIONAL** | May not be statically linked into proprietary modules without open-sourcing the derivative. If used, must run as an isolated standalone CLI process communicating via standard pipes/JSON. |
| **AGPL v3** | **RESTRICTED** | Generally REJECTED unless completely isolated as an external microservice. |
| **Proprietary / No License** | **REJECTED** | Cannot be used, copied, or integrated. |

---

## 4. Credential & Secrets Management

- **Zero Hardcoded Secrets**: Under no circumstances shall API keys, passwords, database credentials, or secret tokens be committed to version control.
- **Environment Isolation**:
  - `.env.example` provides a documented template with sanitized mock defaults.
  - `.env` is permanently excluded via `.gitignore`.
  - Python configuration is managed strictly via `pydantic-settings`, reading from environment variables at startup and failing fast if mandatory values are absent.
- **Static Analysis**: Pre-commit hooks and CI pipelines must run secret scanning (e.g., `detect-secrets` or `gitleaks`) to prevent accidental leaks.

---

## 5. Acquisition Pipeline Safeguards (Phase 3 Implementation)

The Phase 3 acquisition engine incorporates defense-in-depth safeguards:

1. **Redirect Boundary Enforcement**:
   The HTTP fetcher explicitly tracks redirect chains. If an HTTP 301/302 response redirects to a domain not explicitly present in the source's `allowed_domains` list, the request is immediately aborted with a `DisallowedRedirectError`.
2. **Strict Response-Size Bounding**:
   Outbound requests stream responses in chunks. If the cumulative byte count exceeds `max_response_bytes` (e.g., 10MB for articles, 50MB for open dataset archives), the stream is terminated immediately with `ResponseTooLargeError` to prevent memory exhaustion or zip bomb attacks.
3. **MIME Content-Type Validation**:
   Responses are validated against declared `supported_content_types` before payload processing commences. Disallowed binary or unexpected MIME types trigger `ContentTypeMismatchError`.
4. **Guarded Live Smoke Testing**:
   Live endpoint verification (`python -m src.pipeline smoke-test`) is strictly disabled by default. It requires explicit confirmation (`--confirm-live`), preventing unexpected outbound network traffic during offline testing, CI builds, or sandbox runs.
5. **Configurable Retention Controls**:
   All source records enforce a `RetentionPolicy`. Non-redistributable journalism sources store only extractive summaries, headlines, and metadata in relational storage, ensuring raw full texts are not redistributed.
