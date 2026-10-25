# 🎉 EventWise — AI-Powered Multi-Agent Event Orchestration Platform

[![CI Pipeline](https://github.com/Maghnad/EventWise/actions/workflows/ci.yml/badge.svg)](https://github.com/Maghnad/EventWise/actions)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Test Coverage](https://img.shields.io/badge/Coverage->=80%25-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **EventWise** is a full-stack, enterprise-ready event planning and management platform powered by autonomous **Generative AI Multi-Agent Orchestration**. From initial vibe ideation and predictive budget simulation to critical-path timelines, vendor RFP generation, and digital RSVP guest management, EventWise transforms chaotic event planning into an intuitive, seamless workflow.

---

## 📌 Table of Contents

- [Problem Statement \& Value Proposition](#-problem-statement--value-proposition)
- [Key Features \& Capabilities](#-key-features--capabilities)
- [Multi-Agent Architecture](#-multi-agent-architecture)
- [System Architecture Diagram](#-system-architecture-diagram)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [1. Backend Setup](#1-backend-setup)
  - [2. Frontend Setup](#2-frontend-setup)
- [API Documentation](#-api-documentation)
- [Testing \& Quality Assurance](#-testing--quality-assurance)
- [Deployment Guide](#-deployment-guide)
- [Security Hardening Pass](#-security-hardening-checklist)
- [License](#-license)

---

## 💡 Problem Statement & Value Proposition

Planning any event—weddings, corporate summits, galas, hackathons, or private celebrations—is notoriously fragmented, stressful, and error-prone:
1. **Budget Overruns:** Planners struggle with hidden fees, poor category forecasting, and lack of real-time cost impact analysis.
2. **Scheduling Bottlenecks:** Deadlines slip when critical milestone dependencies and vendor lead-times are miscalculated.
3. **Vendor Chaos:** Sourcing reputable vendors, generating detailed questionnaires, and tracking payment milestones consumes dozens of manual hours.
4. **Blank Canvas Paralysis:** Translating abstract themes into cohesive color palettes, decor arrangements, and spatial venue staging is daunting.
5. **Attendee Logistics Overload:** Collecting RSVPs, dietary restrictions, and answering repetitive venue/parking questions drains organizer focus.

**EventWise solves this end-to-end** through specialized, coordinated Generative AI agents that collaborate to construct comprehensive, tailored event plans in seconds.

---

## ✨ Key Features & Capabilities

### 1. 📊 Unified Event Intelligence Dashboard
- **Real-Time Progress Tracking:** Instant visual progress indicators for budget utilization percentage, timeline milestone completion, and vendor checklist tasks.
- **Multi-Event Overview:** Manage concurrent events with categorized badge indicators (Status: Draft, Planning, Confirmed, Completed; Type: Wedding, Conference, Gala, Birthday, Social).
- **Responsive & Accessible Design:** Glassmorphism UI built with WCAG 2.1 AA accessibility standards, responsive mobile layouts, and smooth animations.

### 2. 🤖 Autonomous Multi-Agent Plan Generation
With a single click on **"Generate Event Plan"**, an orchestrated cluster of AI agents works in unison:
- **Planner Agent:** Synthesizes event constraints (type, guest count, location, total budget) into an overarching strategy.
- **Budget Agent:** Automatically partitions total funds into industry-standard line items (Venue, Catering, Photography, Decor, Entertainment, Logistics, Contingency).
- **Timeline Agent:** Backward-schedules milestones from the event date, estimating lead times and task dependencies.
- **Vendor Agent:** Builds customized vendor categories with tailored interview questions, contract considerations, and booking deadlines.

### 3. 💸 Interactive Budget & "What-If" Scenario Simulator
- **Itemized Ledger:** Track planned vs. actual costs with commitment statuses (`Planned`, `Deposit Paid`, `Paid`, `Cancelled`).
- **Predictive Variance Simulator:** Slide guest count and budget variance sliders to simulate real-time financial impact before committing capital.
- **Visual Utilization:** Dynamic warning banners when projected allocations exceed maximum available funds.

### 4. ⏳ Critical-Path Timeline & Milestones
- **Status Workflow:** Transition tasks seamlessly across `Pending`, `In Progress`, `Completed`, and `Delayed`.
- **Milestone Grouping:** Automatic grouping by milestone phases with countdown timers and overdue indicators.
- **Custom Milestone Creation:** Add bespoke tasks with designated due dates and assignees.

### 5. 🤝 Vendor Coordination & Checklist
- **Category Sourcing:** Florists, caterers, lighting, DJs, photographers, and audio-visual specialists.
- **RFP Questionnaires:** Pre-generated domain questions to ask prospective vendors during inquiries.
- **Contract Tracking:** Retain contact info, contract terms, deposit records, and booking deadlines.

### 6. 🎨 Aesthetic Concept & Spatial Moodboard
- **Vibe Concept Generator:** Translates high-level themes into tailored design briefs, atmosphere notes, and curated 5-swatch hex color palettes.
- **Spatial Decor Flow:** Decor recommendations grouped by spatial zones (*Atrium & Entrance*, *Ceremony & Altar*, *Dining & Tablescapes*, *Lounge & Bar*).
- **Generative AI Visual Staging Prompts:** Photorealistic diffusion prompts for 3D visualization and venue moodboarding.

### 7. 💌 Digital RSVP Hub & Public Guest Concierge
- **Public RSVP Portal (`/rsvp/[eventId]`):** Guests submit attendance, plus-ones, and dietary restrictions without requiring user authentication.
- **24/7 Guest FAQ Bot (`GuestFAQBot`):** An AI assistant embedded on the RSVP page that answers guest queries regarding venue address, parking, dress codes, and schedules in real-time.
- **Attendee Roster:** Organizers filter attendees by status (`Attending`, `Declined`, `Tentative`, `Pending`) and export dietary requirements.

### 8. 💬 Conversational Event Planning Concierge
- **Multi-Turn AI Chat (`/dashboard/ai-chat`):** Chat directly with your event assistant equipped with function calling to inspect your active budget, update timelines, or generate creative icebreakers.
- **Context-Aware Memory:** Maintains awareness of selected event parameters throughout multi-turn dialogues.

---

## 🧠 Multi-Agent Architecture

```
                      ┌─────────────────────────┐
                      │    User Request / UI    │
                      └────────────┬────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │    FastAPI API Router   │
                      └────────────┬────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │    Planner Agent (Orch) │
                      └──────┬─────┬─────┬──────┘
                             │     │     │     
         ┌───────────────────┘     │     └───────────────────┐
         ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Budget Agent   │       │  Timeline Agent │       │  Vendor Agent   │
│ (Allocations &  │       │ (Milestones &   │       │ (RFP & Lead     │
│  What-If Sim)   │       │  Dependencies)  │       │  Time Scopes)   │
└─────────────────┘       └─────────────────┘       └─────────────────┘
         │                         │                         │
         └───────────────────┐     │     ┌───────────────────┘
                             ▼     ▼     ▼
                      ┌─────────────────────────┐
                      │ Concept & Moodboard Agt │
                      │ (Palettes, Zones & DALL)│
                      └────────────┬────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │ Database Persistence    │
                      │ (SQLAlchemy ORM 2.0)    │
                      └─────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com) (Python 3.12, fully asynchronous)
- **Database & ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org) async with [Alembic](https://alembic.sqlalchemy.org) migrations
- **Supported Databases:** PostgreSQL (`asyncpg`) & SQLite (`aiosqlite`)
- **Security & Auth:** JWT (`python-jose` with HS256 algorithm pinning), Bcrypt (`passlib`), TOTP 2FA (`pyotp`), Bleach sanitization, SlowAPI rate limiting
- **Testing:** Pytest, pytest-asyncio, pytest-cov (240 tests, >= 80% coverage)

### Frontend
- **Framework:** [Next.js 14](https://nextjs.org) (App Router, React 18, TypeScript)
- **Styling:** Vanilla CSS design system tokens + Tailwind CSS utilities
- **Typography:** Google Fonts (`Inter` via `@next/font/google`)
- **State & Data Fetching:** Custom React hooks (`useAuth`, `useEvents`, `useBudget`, `useTimeline`, `useConcept`)
- **Testing:** Vitest, React Testing Library, `jest-axe` (WCAG compliance), Playwright E2E

### Generative AI Models & Foundation Services
- **Foundation Models:** Google Gemini (`gemini-3.8-flash` / Vertex AI / AI Studio) & OpenAI GPT-4o
- **Structured Generation:** Pydantic schema validation for guaranteed JSON output formatting
- **Graceful Fallbacks:** Built-in resilience with curated demo data for zero-downtime demonstrations

---

## 📂 Project Structure

```
eventwise/
├── app/                           # FastAPI Application Core
│   ├── main.py                    # Entry point, middlewares (CORS, CSRF, security headers)
│   ├── config.py                  # Pydantic Settings & environment validators
│   ├── database.py                # Async SQLAlchemy engine & session factory
│   ├── ai/                        # Multi-Agent Generative AI system
│   │   ├── planner_agent.py       # Master planning orchestrator
│   │   ├── budget_agent.py        # Budget breakdown & what-if simulator
│   │   ├── timeline_agent.py      # Timeline & milestone generation
│   │   ├── vendor_agent.py        # Vendor checklist & inquiry generator
│   │   ├── concept_agent.py       # Theme & color palette generation
│   │   ├── moodboard_agent.py     # Spatial zones & visual staging prompts
│   │   ├── chat_agent.py          # Interactive conversational concierge
│   │   ├── llm_client.py          # Async LLM client with retries & backoff
│   │   └── router.py              # AI endpoints
│   ├── users/                     # Authentication, JWT, and TOTP MFA
│   ├── events/                    # Event CRUD operations
│   ├── budgets/                   # Budget line item tracking
│   ├── timeline/                  # Milestone tracking
│   ├── vendors/                   # Vendor checklist items
│   ├── guests/                    # Guest invitations & public RSVP
│   └── shared/                    # Sanitizer, contracts, logging filters, base models
├── frontend/                      # Next.js 14 Application
│   ├── src/
│   │   ├── app/                   # App Router pages (/dashboard, /login, /signup, /rsvp)
│   │   ├── features/              # Modular domain features (auth, budget, timeline, guests, ai-chat)
│   │   ├── services/              # Centralized API client with CSRF & in-memory auth
│   │   └── shared/                # Accessible UI components (Card, Button, Modal, EmptyState)
│   ├── next.config.mjs            # Production CSP, security headers & source map controls
│   └── package.json               # Frontend dependencies & scripts
├── tests/                         # Backend Pytest test suites (240 tests)
├── .github/workflows/ci.yml       # GitHub Actions CI (Ruff, Mypy, Pytest, Vitest, pip-audit)
├── render.yaml                    # Render production deployment configuration
├── railway.toml                   # Railway production deployment configuration
└── .env.example                   # Environment variable template
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.12+**
- **Node.js 20+** and **npm**
- **Git**

### 1. Backend Setup

```bash
# 1. Clone repository
git clone https://github.com/Maghnad/EventWise.git
cd EventWise

# 2. Create and activate Python virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# 3. Install backend dependencies
pip install -e ".[dev]"

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your OPENAI_API_KEY / GEMINI_API_KEY and random JWT_SECRET

# 5. Run database migrations
alembic upgrade head

# 6. Start backend development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
API will be live at `http://127.0.0.1:8000`. Interactive OpenAPI documentation at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup

In a new terminal window:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install --legacy-peer-deps

# 3. Configure local environment
cp .env.example .env.local

# 4. Start Next.js development server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 📡 API Documentation

EventWise exposes clean RESTful endpoints:

| Domain | Method | Endpoint | Description |
|---|---|---|---|
| **Auth** | `POST` | `/auth/signup` | Register a new user |
| **Auth** | `POST` | `/auth/login` | Authenticate credentials (returns JWT & set HttpOnly cookie) |
| **Auth** | `POST` | `/auth/refresh` | Rotate access & refresh tokens |
| **Auth** | `POST` | `/auth/mfa/setup` | Generate TOTP 2FA secret & QR URI |
| **Auth** | `POST` | `/auth/mfa/verify` | Verify 6-digit TOTP code and enable 2FA |
| **Events** | `GET` | `/api/events` | List all events owned by current user |
| **Events** | `POST` | `/api/events` | Create a new event |
| **Events** | `GET` | `/api/events/{id}` | Get event details with stats summary |
| **AI Planner** | `POST` | `/events/{id}/generate-plan` | Generate complete multi-agent plan |
| **AI Budget** | `POST` | `/events/{id}/what-if` | Run predictive budget scenario simulation |
| **AI Concept** | `POST` | `/api/events/{id}/concept` | Generate design brief & color palettes |
| **AI Moodboard**| `POST` | `/api/events/{id}/moodboard` | Generate spatial zone decor & visual prompts |
| **AI Chat** | `POST` | `/events/{id}/chat` | Multi-turn planning assistant dialogue |
| **RSVP** | `POST` | `/guests/{eventId}/rsvp` | Public guest attendance submission |
| **RSVP Bot** | `POST` | `/guests/{eventId}/faq-bot` | Public 24/7 guest concierge FAQ chat |

---

## 🧪 Testing & Quality Assurance

EventWise features 100% passing test coverage across both backend and frontend layers:

```bash
# Run backend test suite (240 tests with coverage check >= 80%)
pytest --cov=app --cov-fail-under=80

# Run frontend unit & component tests (38 tests)
cd frontend
npm test -- --run

# Run accessibility (a11y) checks
npm run test:a11y

# Run end-to-end user flow test (Playwright)
npm run test:e2e
```

---

## 🛡️ Security Hardening Checklist

EventWise has undergone an exhaustive 21-point security hardening audit:

| # | Security Category | Hardening Measure | Status |
|---|---|---|:---:|
| 1 | **SQL Injection Protection** | 100% SQLAlchemy 2.0 ORM parameterized query usage; zero raw string interpolation; strict linting policies in `app/database.py`. | ✅ Hardened |
| 2 | **Cross-Site Scripting (XSS)** | Input sanitization using `bleach` stripping tags and attributes on event titles, descriptions, chats, notes, and guest inputs; zero `dangerouslySetInnerHTML` on frontend. | ✅ Hardened |
| 3 | **CSRF Defense** | Non-HttpOnly `csrf_token` cookie + `X-CSRF-Token` header verification on mutating HTTP requests (`POST`, `PUT`, `PATCH`, `DELETE`); automated injection via frontend API client. | ✅ Hardened |
| 4 | **File Upload Security** | Verified zero unstructured user file uploads in production scope. | N/A |
| 5 | **BOLA / IDOR Prevention** | Strict resource tenant checks (`resource.user_id == current_user.id` or 404/403) across events, budgets, timeline items, vendors, and guests. UUIDv4 primary keys throughout. | ✅ Hardened |
| 6 | **Rate Limiting** | SlowAPI rate limiting active on `/auth/*` (5/min), AI endpoints (10/min), and general API (100/min); returns HTTP 429 with `Retry-After: 60` headers. | ✅ Hardened |
| 7 | **JWT Hardening** | Short 15-minute access token TTL; pinned `algorithms=["HS256"]` explicitly on encode/decode; mandatory token claims (`exp`, `iss`, `aud`); production startup crash on weak/default secrets. | ✅ Hardened |
| 8 | **Secret Segregation** | Zero credentials in frontend repository; only `NEXT_PUBLIC_*` public variables exposed to browser; all secrets isolated to server-side `.env`. | ✅ Hardened |
| 9 | **Cryptographic Password Hashing** | Bcrypt with salt verification via `passlib`; zero plaintext persistence; passwords excluded from serialization models and logs. | ✅ Hardened |
| 10 | **Multi-Factor Authentication (MFA)** | TOTP-based 2FA endpoints (`POST /auth/mfa/setup`, `POST /auth/mfa/verify`) leveraging `pyotp` with 32-character base32 secrets and QR provisioning URLs. | ✅ Hardened |
| 11 | **CORS Lockdown** | Wildcard `*` prohibited in production; exact origin allowlists loaded from `CORS_ORIGINS`; dynamic localhost regex in development. | ✅ Hardened |
| 12 | **Security Headers** | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Content-Security-Policy`, and HSTS on both FastAPI backend and Next.js frontend. | ✅ Hardened |
| 13 | **In-Memory Token Storage** | Eliminated `localStorage`/`sessionStorage` JWT storage; access token held strictly in ephemeral React memory; refresh token held in secure `HttpOnly` `SameSite=Lax` cookies. | ✅ Hardened |
| 14 | **Server-Side Authorization** | Complete authorization enforcement via FastAPI dependencies and domain services; client-side route guards serve purely as UX enhancements. | ✅ Hardened |
| 15 | **Row-Level Security (RLS)** | App-level tenant isolation enforced on every query filter (`owner_id == user.id`), ready for database RLS policies. | ✅ Hardened |
| 16 | **Webhook Verification** | No external inbound webhooks currently configured. | N/A |
| 17 | **SSRF Defense** | No endpoints accept arbitrary external outbound URLs. | N/A |
| 18 | **Source Map Concealment** | Frontend configured with `productionBrowserSourceMaps: false` in `next.config.mjs`; backend serves zero map files in production. | ✅ Hardened |
| 19 | **Default Credential Elimination** | Zero hardcoded default administrative passwords or seeds; all credentials require explicit runtime configuration. | ✅ Hardened |
| 20 | **Sensitive Log Redaction** | Custom `SensitiveDataRedactor` logging filter masks passwords, bearer tokens, API keys, and secret values with `[REDACTED]`. | ✅ Hardened |
| 21 | **Dependency Vulnerability Scanning** | Integrated `pip-audit` for backend dependencies and `npm audit` for frontend dependencies in GitHub Actions CI pipeline (`.github/workflows/ci.yml`). | ✅ Hardened |

---

## 🚢 Deployment Guide

### Deploy Backend (Render / Railway)
- **Render:** Connect the repo and use [render.yaml](file:///c:/Users/debna/Downloads/event_management/render.yaml). It automatically configures the Python 3.12 environment, runs migrations, and launches `uvicorn app.main:app`.
- **Railway:** Uses [railway.toml](file:///c:/Users/debna/Downloads/event_management/railway.toml) for automatic PostgreSQL database provisioning and web deployment.

### Deploy Frontend (Vercel)
- Import the `frontend/` directory into [Vercel](https://vercel.com).
- Add `NEXT_PUBLIC_API_BASE_URL` pointing to your deployed backend.
- Headers and routing configurations are pre-defined in [frontend/vercel.json](file:///c:/Users/debna/Downloads/event_management/frontend/vercel.json).

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](file:///c:/Users/debna/Downloads/event_management/LICENSE) file for details.
