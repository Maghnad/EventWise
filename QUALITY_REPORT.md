# EventWise — Quality & Submission Report

**Date:** October 29, 2026  
**Status:** Ready for Submission  
**Total Test Suite:** 278 Tests Passing (240 Backend Pytest + 38 Frontend Vitest)  
**Overall Backend Coverage:** 91% (All services and agents ≥ 87%)  

---

## 1. Feature-to-Problem Mapping

Event planning is notoriously stressful, fragmented, and vulnerable to costly missteps. EventWise directly maps each core feature to a concrete operational pain point:

| Problem in Event Planning | EventWise Feature | Technical Solution & Architecture |
| :--- | :--- | :--- |
| **Blank-page paralysis & disjointed aesthetic themes** | **Concept Board Agent** (`POST /events/{id}/concept`) | Uses Generative AI structured JSON synthesis (`ConceptBoard`) to create cohesive color swatches, decor motifs, layout ideas, and milestones from high-level vibe briefs. |
| **Vague decor ideas and high vendor design markup** | **Moodboard & Spatial Styling Agent** (`POST /events/{id}/moodboard`) | Generates zone-by-zone spatial decor items with cost estimations and precise Generative AI diffusion visual staging prompts. |
| **Budget creep & hidden fees** | **Smart Budget Agent & What-If Simulator** (`POST /events/{id}/what-if`) | GenAI-driven dynamic allocation across categories with live scenario simulation calculating per-guest spend variance and delta analysis. |
| **Missed booking deadlines & vendor oversight** | **Vendor Checklist Agent** (`app/ai/vendor_agent.py`) | Categorizes vendors, calculates reverse booking lead-time days from event date, and pre-populates critical interview questions via GenAI. |
| **Scattered planning schedules & panic before event** | **Timeline Agent & Interactive Gantt** (`POST /events/{id}/generate-plan`) | Generates chronological countdown milestones relative to event date and auto-persists tasks into the database using Generative AI. |
| **Generic, cookie-cutter event suggestions** | **Vector RAG Creative Ideas Agent** (`POST /events/{id}/ideas`) | Computes semantic vector embeddings of vendor and past event datasets with cosine similarity retrieval to inject hyper-personalized suggestions. |
| **Context switching across tools & lack of guidance** | **Conversational Planning Assistant** (`POST /events/{id}/chat`) | Multi-turn conversational GenAI agent with conversation memory and function-calling tools (`budget_planner`, `timeline_planner`, `vendor_checklist`). |
| **RSVP drop-off & repetitive guest inquiries** | **Public RSVP & Guest FAQ Bot** (`/rsvp/[eventId]`) | Zero-auth public RSVP pages with instant dietary capture and automated heuristic FAQ bot answering venue, dress code, and timing queries. |
| **Lack of high-level progress visibility** | **Real-Time Executive Dashboard** (`/dashboard`) | Progress tracking showing budget spent, timeline task completion, vendor checklist status, and quick-action access. |

---

## 2. Code Quality & Linting Audit

### Backend Quality Checks
- **Linter & Formatter (`ruff`):**
  - Configuration: `pyproject.toml` (target Python 3.12, rules `E`, `F`, `I`, `N`, `UP`, `B`, `SIM`, `RUF`).
  - Result: `All checks passed!` with 0 errors across all modules.
- **Type Safety (`mypy`):**
  - Strict type hints with Pydantic v2 validation across contracts, schemas, and models.
- **Module Boundary & Architectural Integrity:**
  - Automated tests in `tests/unit/test_module_boundaries.py` verify acyclic graph (`DAG`), zero circular imports, and strict layer isolation (shared layer does not depend on services/routers; services do not depend on routers).

### Frontend Quality Checks
- **ESLint (`eslint-config-next` + `eslint-plugin-jsx-a11y`):**
  - Result: `✔ No ESLint warnings or errors`.
- **TypeScript:**
  - Full TypeScript strict mode enabled with zero implicit `any`.
- **Prettier:**
  - Standardized code style and Tailwind class sorting.

---

## 3. Test Coverage Breakdown

### Backend (`pytest --cov=app tests/`)
- **Total Tests:** 240 passed in 44.78s
- **Total Statements:** 3,195
- **Statements Covered:** 2,901
- **Overall Coverage:** **91%**

#### Services & Agents Coverage Summary (Target ≥ 80%)

| Service / Agent | File Path | Coverage |
| :--- | :--- | :--- |
| **Event Service** | `app/events/service.py` | **100%** |
| **Guest Service** | `app/guests/service.py` | **97%** |
| **Budget Service** | `app/budgets/service.py` | **96%** |
| **Timeline Service** | `app/timeline/service.py` | **96%** |
| **Vendor Service** | `app/vendors/service.py` | **95%** |
| **User / Auth Service** | `app/users/service.py` | **93%** |
| **Budget Agent** | `app/ai/budget_agent.py` | **100%** |
| **Concept Agent** | `app/ai/concept_agent.py` | **100%** |
| **Moodboard Agent** | `app/ai/moodboard_agent.py` | **100%** |
| **Planner Agent (LangGraph)**| `app/ai/planner_agent.py` | **100%** |
| **Vendor Agent** | `app/ai/vendor_agent.py` | **100%** |
| **Chat Agent** | `app/ai/chat_agent.py` | **99%** |
| **Timeline Agent** | `app/ai/timeline_agent.py` | **98%** |
| **Base Agent** | `app/ai/base_agent.py` | **95%** |
| **Agent Tools** | `app/ai/tools/__init__.py` | **94%** |
| **LLM Client (Exponential Backoff)** | `app/ai/llm_client.py` | **90%** |
| **Ideas Agent (pgvector RAG)** | `app/ai/ideas_agent.py` | **87%** |

### Frontend (`vitest run`)
- **Total Tests:** 38 passed across 8 test suites:
  - `EventForm.test.tsx` (5/5 passed)
  - `BudgetBreakdown.test.tsx` (5/5 passed)
  - `WhatIfPanel.test.tsx` (5/5 passed)
  - `TimelineView.test.tsx` (4/4 passed)
  - `VendorChecklist.test.tsx` (6/6 passed)
  - `ChatWindow.test.tsx` (5/5 passed)
  - `ConceptForm.test.tsx` (5/5 passed)
  - `index.test.ts` (3/3 passed)

---

## 4. Accessibility (a11y) Audit

Every frontend component was subjected to automated WCAG 2.1 AA accessibility audits using `jest-axe`:
- **`jest-axe` Checks:** 0 violations across `EventForm`, `BudgetBreakdown`, `WhatIfPanel`, `TimelineView`, `VendorChecklist`, `ChatWindow`, and `ConceptForm`.
- **Semantic HTML & Landmarks:** Form groups utilize native `<label htmlFor="...">`, input elements include descriptive `aria-describedby` and `aria-invalid` bindings.
- **Dynamic Updates:** The AI Chat window and live What-If calculations employ `aria-live="polite"` and `role="status"` to announce updates to screen readers without disruptive interruptions.
- **Keyboard Navigation:** Modals trap focus, buttons include visible `:focus-visible` outline rings, and dialogs close on `Escape`.
- **Color Contrast:** Curated modern glassmorphic palette with minimum 4.5:1 text-to-background contrast ratio.

---

## 5. Security & Isolation Measures

1. **Authentication & Password Hashing:**
   - Passwords securely hashed with `bcrypt` (12 rounds) using `passlib`.
   - Stateless JWT tokens signed with `HS256`, configurable expiration and bearer scheme.
2. **Multi-Tenant Ownership Isolation:**
   - Every database query for events, budgets, tasks, vendors, and guests filters explicitly by `owner_id` or verifies parent event ownership.
   - Cross-tenant access triggers HTTP 404 to avoid leaking resource existence.
3. **Rate Limiting (SlowAPI):**
   - Authentication routes: `5/minute` on signup and login to mitigate brute force attacks.
   - Plan generation: `10/minute`.
   - Concept, Moodboard, Ideas, What-If: `20/minute`.
   - AI Chat: `30/minute`.
4. **CORS Configuration:**
   - Restricted to explicit origins configured via `CORS_ORIGINS` (supporting comma-separated and JSON strings).
5. **No Committed Secrets:**
   - Zero hardcoded API keys or passwords.
   - `.gitignore` strictly ignores `.env`, `.env.*`, `*.db`, `*.sqlite`, and credentials.
6. **Container Security:**
   - Docker multi-stage build running under an unprivileged `appuser` system account.
   - Built-in HTTP health check endpoint (`/health`).
7. **Cross-Site Scripting (XSS) Prevention & HTTP Security Headers:**
   - **Context-Aware Output Escaping:** React automatically escapes all dynamic content rendered in JSX; zero `dangerouslySetInnerHTML` instances exist across the entire frontend.
   - **Content Security Policy (CSP):** Enforced via Next.js HTTP headers restricting script origins, preventing unauthorized script execution, and forbidding framing (`frame-ancestors 'none'`).
   - **Defensive HTTP Headers:** Both Next.js and FastAPI enforce `X-Content-Type-Options: nosniff` (blocking MIME confusion), `X-Frame-Options: DENY` (clickjacking protection), and `X-XSS-Protection: 1; mode=block`.
   - **Typed Schema Enforcement:** FastAPI strictly deserializes requests into Pydantic models with strict typing, returning only `application/json; charset=utf-8` to eliminate script injection.

---

## 6. Performance & Optimization

- **Database Queries:** All list queries use targeted indexed lookups. No N+1 child queries exist; summaries and breakdowns are calculated in unified queries or single-pass aggregations.
- **Next.js Code Splitting:** Dynamic route chunking produces lightweight initial bundles (First Load JS shared: 87.3 kB).
- **Asset Optimization:** Next.js `<Image />` component with lazy loading, modern formats (`webp`/`avif`), and responsive `sizes`.
- **Resilient GenAI Calling:** `LLMClient` implements exponential backoff with jitter (up to 3 retries) and handles GenAI provider `RateLimitError` and `APIConnectionError` gracefully.
