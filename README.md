# 🎉 EventWise — GenAI-Powered Event Planning Assistant

[![CI Pipeline](https://github.com/Maghnad/EventWise/actions/workflows/ci.yml/badge.svg)](https://github.com/Maghnad/EventWise/actions)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Coverage](https://img.shields.io/badge/Coverage-90.80%25-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **One-line tagline:** Plan weddings, birthdays, and community events with AI-generated budgets, timelines, vendor checklists, and personalized ideas.

---

## 🎯 Problem Statement

**The Problem:** Planning events (weddings, birthdays, corporate summits, community gatherings) is fragmented, chaotic, and overwhelming. Organizers juggle disconnected spreadsheets for budgets, scattered notes for critical timelines, and messy messaging threads for vendor coordination. There is no unified, intelligent platform that turns an abstract "vibe brief" into an executable, end-to-end plan.

**Our Solution:** EventWise uses autonomous Generative AI multi-agent orchestration to transform a short vision brief into an actionable event plan — automatically generating category-partitioned budgets, reverse-scheduled milestone timelines, vendor RFP checklists, spatial moodboards, and an interactive guest RSVP portal, all in one cohesive workspace.

---

## ✨ Features (Mapped to Problem Statement)

| Problem Statement Requirement | Feature | How It Works |
|---|---|---|
| **Budgets** | **AI Budget Planner & What-If Simulator** | User inputs event type, guest count, and total budget ➔ AI allocates category-wise line items with mathematical constraints + real-time slider scenario simulation. |
| **Timelines** | **AI Milestone Timeline Generator** | AI reverse-schedules milestones counting back from the event date, auto-assigning lead times, priority levels, and category tags. |
| **Vendor Checklists** | **Vendor RFP & Inquiry Scopes** | AI produces categorized vendor checklists (Venue, Catering, Florist, Photography, DJ) complete with domain-specific questions to ask before booking. |
| **Personalized Ideas** | **Aesthetic Concept & Spatial Moodboard** | AI synthesizes design narratives, 5-swatch hex color palettes, spatial zone decor recommendations, and diffusion staging prompts. |
| **Weddings / Birthdays / Community** | **Dynamic Event Management Wizard** | Multi-event dashboard supporting weddings, birthdays, conferences, galas, and social meetups with localized status tracking. |
| **"Planning Assistant"** | **Interactive AI Chat Concierge** | Multi-turn conversational assistant with function calling to dynamically inspect budgets, adjust timelines, or brainstorm party themes. |
| **Guest Logistics** | **Public RSVP Hub & 24/7 Guest Bot** | Dedicated public RSVP link (`/rsvp/[eventId]`) with plus-one tracking, dietary restrictions, and an embedded FAQ chatbot for venue/parking queries. |

---

## 🏗️ Architecture

```text
┌────────────────────────────────────────────────────────┐
│           Next.js 14 Frontend (Vercel)                 │
│      TypeScript • Tailwind CSS • App Router            │
└───────────────────────────┬────────────────────────────┘
                            │ HTTPS / REST API
                            ▼
┌────────────────────────────────────────────────────────┐
│            FastAPI Backend (Render)                    │
│      Python 3.12 • SlowAPI • Pydantic v2               │
└─────────────┬───────────────────────────┬──────────────┘
              │                           │
              ▼                           ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   LangGraph Multi-Agent  │  │   Async SQLAlchemy 2.0   │
│ ┌──────────────────────┐ │  │   PostgreSQL / SQLite    │
│ │ Planner Orchestrator │ │  │ ┌──────────────────────┐ │
│ └──────────┬───────────┘ │  │ │ Events & Budgets     │ │
│   ┌────────┴────────┐    │  │ │ Timeline & Vendors   │ │
│   ▼        ▼        ▼    │  │ │ Guests & RSVPs       │ │
│ Concept  Budget  Timeline│  │ │ Users & JWT Auth     │ │
│   │        │        │    │  │ └──────────────────────┘ │
│   └────────┬────────┘    │  └──────────────────────────┘
│            ▼             │
│      Vendor Agent        │
│ └──────────────────────┘ │
│            │             │
│            ▼             │
│ Google Gemini / GPT-4o   │
└──────────────────────────┘
```

---

## 📁 Project Structure

```text
eventwise/
├── app/                           # FastAPI Application Core
│   ├── main.py                    # Entry point, CORS, CSRF, security headers
│   ├── config.py                  # Pydantic Settings & environment validators
│   ├── database.py                # Async SQLAlchemy engine & session factory
│   ├── ai/                        # Multi-Agent Generative AI system
│   │   ├── planner_agent.py       # LangGraph master planning orchestrator
│   │   ├── budget_agent.py        # Budget breakdown & what-if simulator
│   │   ├── timeline_agent.py      # Reverse-scheduled timeline milestones
│   │   ├── vendor_agent.py        # Vendor RFP checklist & inquiry generator
│   │   ├── concept_agent.py       # Theme, vibe summary & color palettes
│   │   ├── moodboard_agent.py     # Spatial decor zones & diffusion prompts
│   │   ├── chat_agent.py          # Conversational planning concierge
│   │   ├── llm_client.py          # Async LLM client with retries & backoff
│   │   └── router.py              # AI API endpoints
│   ├── users/                     # JWT authentication, Bcrypt & TOTP MFA
│   ├── events/                    # Event CRUD service & routes
│   ├── budgets/                   # Budget line item tracking & ledger
│   ├── timeline/                  # Critical-path milestone tasks
│   ├── vendors/                   # Vendor coordination & tracking
│   ├── guests/                    # Guest invitations & public RSVP portal
│   └── shared/                    # Bleach sanitizer, logging filters, base models
├── frontend/                      # Next.js 14 Client Application
│   ├── src/
│   │   ├── app/                   # App Router pages (/dashboard, /login, /signup, /rsvp)
│   │   ├── features/              # Domain modules (auth, budget, timeline, guests, ai-chat)
│   │   ├── services/              # Typed API client with CSRF & in-memory auth
│   │   └── shared/                # Accessible design system components (Card, Button, Modal)
│   ├── next.config.mjs            # Production CSP, security headers & source map controls
│   └── package.json               # Dependencies and scripts
├── tests/                         # Pytest test suite (240 unit & integration tests)
├── .github/workflows/ci.yml       # GitHub Actions CI (Ruff, Mypy, Pytest, Vitest)
├── render.yaml                    # Render production backend deployment config
└── .env.example                   # Environment variable template
```

---

## 🚀 Live Demo

- **Live Frontend URL:** [https://event-wise-ten.vercel.app/](https://event-wise-ten.vercel.app/)
- **Live Backend API Docs:** [https://eventwise.onrender.com/docs](https://eventwise.onrender.com/docs)
- **Demo Credentials:**
  - **Email:** `demo@eventwise.app`
  - **Password:** `DemoPass123!`

---

## 🛠️ Setup (Local)

### 1. Backend

```bash
# Clone repository
git clone https://github.com/Maghnad/EventWise.git
cd EventWise

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install backend dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
Backend API will be live at `http://127.0.0.1:8000` (interactive documentation at `http://127.0.0.1:8000/docs`).

### 2. Frontend

```bash
# In a new terminal:
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Run Next.js development server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🔒 Security Measures

- **Authentication & MFA:** Pinned HS256 JWT access tokens held in ephemeral memory + secure `HttpOnly` refresh cookies + TOTP 2FA (`pyotp`).
- **Authorization & BOLA Defense:** Strict tenant verification (`resource.owner_id == user.id`) on every data query; UUIDv4 primary keys throughout.
- **Input Sanitization:** Automated HTML tag and attribute stripping on all text fields using `bleach`; zero `dangerouslySetInnerHTML` on frontend.
- **CSRF Protection:** Double-submit cookie pattern with `X-CSRF-Token` headers verified on all mutating HTTP requests.
- **Rate Limiting:** SlowAPI token bucket limiting on `/auth` (5/min), AI generation (10/min), and general endpoints (100/min).
- **Defense-in-Depth Headers:** Strict Content Security Policy (CSP), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and HSTS.
- **Zero Secrets in Code:** Strict environment variable isolation; passwords salted and hashed with `bcrypt`.

---

## 🧪 Testing & Quality Assurance

- **Backend:** 240 automated tests with **90.09% code coverage** (`pytest --cov=app --cov-fail-under=80`).
- **Frontend:** 38 unit & component tests passing via Vitest + React Testing Library (`npm test`).
- **Type Safety & Linting:** Strict static type enforcement with `mypy` and linting with `ruff`.
- **CI Pipeline:** Automated GitHub Actions workflow testing every pull request across Python 3.12 and Node 20.

---

## ♿ Accessibility

- **WCAG 2.1 AA Compliant:** High-contrast color tokens, clear focus rings, and readable font scales.
- **Semantic HTML & ARIA:** Descriptive landmarks (`<main>`, `<nav>`, `<header>`), explicit form labels, and modal aria-dialog attributes.
- **Keyboard Navigable:** Full keyboard support for all modals, drawers, dropdowns, and form submissions.

---

## 📊 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS |
| **Backend** | FastAPI, Python 3.12, Pydantic v2 |
| **AI / Multi-Agent** | LangGraph, LangChain, Google Gemini (`gemini-3.8-flash`) / OpenAI GPT-4o |
| **Database & ORM** | SQLAlchemy 2.0 (Async), Alembic, PostgreSQL / SQLite (`aiosqlite`) |
| **Auth & Security** | JWT, Bcrypt, PyOTP (TOTP 2FA), Bleach, SlowAPI |
| **Testing** | Pytest, pytest-cov, pytest-asyncio, Vitest, React Testing Library |
| **Deployment** | Vercel (Frontend) + Render (Backend) |
