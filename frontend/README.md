# T20 Cricket Intelligence Dashboard (Phase 6C)

A polished, research-oriented React dashboard for exploring cricket matches, player performance, media coverage, editorial narratives, topic clusters, cross-source event alignments, source provenance, and the Attention-to-Performance Discrepancy Index (APDI).

---

## 1. Technology Stack

- **Framework**: React 18 with TypeScript 5 (Strict Mode)
- **Bundler & Dev Server**: Vite 6
- **Styling**: Tailwind CSS 3 (Cricket pitch emerald, crimson wicket, dark navy palette)
- **Navigation & Routing**: React Router DOM 6
- **Server State & Caching**: TanStack React Query 5
- **HTTP Client**: Axios with centralized error handling & base URL configuration
- **Visualizations**: Recharts (responsive SVG charts with dark-mode compatibility)
- **Icons**: Lucide React
- **Testing**: Vitest & React Testing Library (JSDOM environment)

---

## 2. Prerequisites

- **Node.js**: `v18+` (Tested on `v22.19.0`)
- **Package Manager**: `npm` (`10.9.3`)
- **Backend API**: The FastAPI server running locally at `http://127.0.0.1:8000`

---

## 3. Local Development Setup

### Install Dependencies
```bash
cd frontend
npm install
```

### Configure Environment Variables
By default, the Vite dev server proxies requests (`/api`, `/health`, `/ready`) directly to `http://127.0.0.1:8000`.

To point to an explicit remote or custom API URL, create a `.env.local` file inside `frontend/`:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Start Development Server
```bash
npm run dev
```
The application will be accessible at `http://localhost:5173`.

---

## 4. Quality Gates & Validation Scripts

### Run Type Checking
```bash
npm run typecheck
```
Executes `tsc --noEmit` with strict TypeScript compiler options.

### Run Unit & Integration Tests
```bash
npm run test
```
Executes Vitest tests covering:
- API client URL and query parameter handling.
- Application shell, routing, and navigation layout.
- APDI `INSUFFICIENT_DATA` safeguards and `null` score preservation.
- Honest unpopulated corpus empty states.
- System Health 4-tier diagnostic verification.

### Production Build
```bash
npm run build
```
Generates production-optimized bundle in `frontend/dist/`.

---

## 5. Architectural Integrity & Safeguards

1. **No Data Fabrication**: When the underlying SQLite database contains 0 tournament records, all pages display clear, structured empty-state notices. No synthetic scores, fake players, or invented results are ever rendered.
2. **APDI Preservation**: Entities with sample sizes below statistical evidence thresholds are classified as `INSUFFICIENT_DATA`. Their discrepancy score is strictly displayed as `unavailable` (`null`), never coerced to `0` or `0.0`.
3. **Four-Tier Diagnostic System**: The System Health page monitors Process Liveness, Persistence Readiness, Data Inventory, and Analytical Sufficiency independently, ensuring no generic false-positive green badge obscures an unpopulated corpus.
