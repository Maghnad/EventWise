# 🎉 EventWise

> **State-of-the-Art Multi-Agent Generative AI Event Orchestration Platform** — powered by FastAPI, Next.js 14, and Generative AI Foundation Models.

## 🤖 Generative AI Architecture & Technologies

EventWise leverages advanced **Generative AI (GenAI)** throughout the entire event lifecycle:
- **GenAI Multi-Agent Orchestration (LangGraph):** Autonomous planning graph connecting Budget, Timeline, Vendor, and Concept agents with typed JSON structured generation.
- **GenAI Visual Staging & Diffusion Prompts:** Automated spatial zone decor planning paired with photorealistic GenAI diffusion prompts for atmospheric venue rendering.
- **GenAI Vector RAG (Retrieval-Augmented Generation):** High-dimensional semantic embeddings with pgvector similarity search for hyper-personalized event ideas.
- **Conversational GenAI Planning Assistant:** Multi-turn interactive conversational agent with function calling and dynamic tool invocation.
- **GenAI Scenario Simulator:** Real-time budget and guest variance simulation with predictive cost impact analysis.

## Quick Start

```bash
# 1. Create & activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Copy env template and fill in secrets
cp .env.example .env

# 4. Run database migrations
alembic upgrade head

# 5. Start the dev server
uvicorn app.main:app --reload
```

The API will be available at **http://localhost:8000**.
Interactive docs at **http://localhost:8000/docs**.


## Project Structure

```
app/
├── main.py          # FastAPI app, CORS, router includes
├── config.py        # Pydantic Settings (reads .env)
├── database.py      # Async SQLAlchemy engine & session
├── users/           # User accounts & authentication
├── events/          # Event CRUD
├── budgets/         # Budget tracking
├── timeline/        # Timeline / milestones
├── vendors/         # Vendor management
├── ai/              # Multi-Agent Generative AI Architecture & RAG
└── shared/          # Cross-cutting utilities & base models
```


## 🛡️ Security Hardening Checklist

EventWise has undergone a comprehensive defense-in-depth security hardening review across all 21 critical areas:

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
| 11 | **CORS Lockdown** | Wildcard `*` prohibited in production; exact origin allowlists loaded from `CORS_ORIGINS`; explicit allowed HTTP methods and headers. | ✅ Hardened |
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

## License

MIT

