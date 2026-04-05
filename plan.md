# Energy Optimization SaaS (React + FastAPI + Mongo) — Phased Plan (Updated)

## 1) Objectives
- Deliver a sellable V1 SaaS for PMI (single site) that demonstrates **real economic impact** via: anomaly/waste detection, smart advice with ROI/payback, and cost prediction.
- Use the current stack **React + FastAPI + MongoDB** while keeping a SaaS-ready structure (org/site scoping, roles-ready, audit-friendly).
- Ship V1 with real integrations:
  - **Google OAuth** (start + callback)
  - **OpenWeather** weather enrichment
  - **Energy price signal** via `energy-charts` (IT-North)
  - **Email notification flow** in **development-mode** (internal logging) acceptable for V1
- Keep the product minimal, fast, and “Stripe-like” in UX: clarity on € impact, simple onboarding, and actionable next steps.

**Current status:** Phase 1 and Phase 2 are completed. The app is a working end-to-end V1 with docs and E2E test validation.

---

## 2) Implementation Steps

### Phase 1 — Core Workflow POC (Isolation) ✅ COMPLETED
**Goal:** Prove end-to-end core logic works with real inputs and integrations, via scripts + minimal API.

**Status notes (what’s done):**
- Implemented and validated POC core pipeline:
  - Manual energy data ingestion
  - PDF-ready bill upload flow with secure local storage + best-effort parsing (and conceptual “needs manual review” fallback)
  - Weather enrichment
  - Energy price signal enrichment
  - Anomaly detection
  - Smart advice generation including ROI/payback
  - KPI generation
  - Cost prediction + alert flag
- Implemented backend POC files:
  - `/app/backend/server.py`
  - `/app/backend/energy_core.py`
  - `/app/scripts/poc_core_flow.py`
- Real integrations validated:
  - OpenWeather integration working end-to-end in POC
  - Energy prices integration working via `https://api.energy-charts.info/price?bzn=IT-North` (EUR/MWh converted to EUR/kWh)
- Testing validated:
  - Testing agent report: `/app/test_reports/iteration_1.json` shows **100% backend pass** for Phase 1 endpoints.

**Deliverables shipped (Phase 1):**
- Script: `/app/scripts/poc_core_flow.py` produces a JSON report proving the end-to-end flow.
- POC endpoints available under `/api/poc/*` (retained for regression/demo):
  - `GET /api/poc/contracts`
  - `POST /api/poc/ingest-manual`
  - `POST /api/poc/upload-bill`
  - `POST /api/poc/run-analysis`
  - `GET /api/poc/latest-analysis`

**Exit criteria:** Met.

---

### Phase 2 — V1 Working App (Full Frontend + Core SaaS Backend + Required Integrations) ✅ COMPLETED
**Goal:** Turn the validated POC into a usable V1 product: full SaaS UX for PMI single-site, with required integrations (Google OAuth, weather/prices enrichment, notifications incl. dev-mode email), and a backend structure scalable to multi-site later.

#### 2.1 Scope (what we built in V1)
**Frontend (React + Tailwind + shadcn/ui + Recharts)**
- **Authentication**
  - Google OAuth login (via backend start/callback)
  - **Dev/test bypass** login for agent/browser testing (non-production)
- **Onboarding wizard (single-site PMI-first)**
  - Company + sector
  - Site location (lat/lon, city) + business hours
  - First data: upload PDF or manual batch
  - Savings goal + summary
- **Core pages shipped**
  - Dashboard: KPIs + charts + top advice + anomalies + integration status
  - Bills: upload/list + review/correction dialog for extracted fields
  - Consumption: manual entry + batch import + table + delete
  - Insights: anomaly timeline filters + advice cards with ROI/payback + forecast block
  - Reports: generate + list + PDF download
  - Pricing: Free/Pro UI only (no billing)
  - Settings: notification preferences, integration summary, dev-mode email test, logout
  - Notifications center in AppShell (sheet) + mark-all-read

**Backend (FastAPI + MongoDB)**
- SaaS-ready entities/collections:
  - `users`, `orgs`, `sites`
  - `bills`, `consumption_readings`, `analytics_runs`
  - `notifications`, `notification_preferences`, `notification_events`
  - `reports`
- **Auth**
  - `POST /api/auth/dev-login`
  - `GET /api/auth/google/start` (302 redirect)
  - `GET /api/auth/google/callback` (creates session cookie and redirects)
  - `GET /api/auth/me`, `POST /api/auth/logout`
- **Onboarding**
  - `GET /api/onboarding/state`, `POST /api/onboarding/complete`
- **Bills**
  - Upload + list + detail + patch review (`/api/bills/*`)
- **Consumption**
  - Single create, batch create, list, delete (`/api/consumption/*`)
- **Analytics + Dashboard**
  - `POST /api/analytics/run`
  - `GET /api/analytics/latest`
  - `GET /api/dashboard/overview`
- **Notifications**
  - list, mark-all-read, preferences, dev-mode test email
- **Reports**
  - generate PDF from latest analysis + list + download
- **Integrations**
  - OpenWeather weather (cached)
  - energy-charts price signal (cached) + fallback
  - email delivery: dev-mode internal logging (`notification_events`)
- POC endpoints retained under `/api/poc/*` for regression.

**Documentation shipped (under `/app/docs`)**
- `PROJECT_STRUCTURE.md`
- `DATABASE_SCHEMA.md`
- `API_ENDPOINTS.md`
- `ALGORITHMS_AND_UI.md`
- `DEPLOY_AND_ROADMAP.md`

#### 2.2 Shipped user stories (Phase 2) ✅
**Auth & onboarding**
1. Sign in via dev bypass and reach app.
2. Start Google OAuth login and complete callback flow (credentials configured).
3. Complete onboarding wizard (company/site/hours/savings goal) and land on dashboard.

**Data ingestion**
4. Upload a bill PDF, store it, and view extraction status.
5. Review/correct extracted fields (kWh, € total, period) via UI.
6. Insert consumption readings manually (single) and via batch import; delete entries.

**Analytics & value delivery**
7. Run analysis and see KPIs, anomalies, prioritized advice with ROI/payback.
8. View forecast next 30 days with variation and alert.
9. Inspect insights page with anomaly timeline and advice cards.

**Notifications & reporting**
10. Receive in-app notifications generated after analysis.
11. Mark all notifications as read.
12. Enable dev-mode “email” alerts and send a test event (logged).
13. Generate and download a monthly PDF report.

**Productization**
14. View Pricing (Free/Pro) UI and upgrade CTA dialog (no billing).
15. Settings page shows integration status and notification preferences.

#### 2.3 Testing results (Phase 2) ✅
- `/app/test_reports/iteration_2.json`
  - Comprehensive E2E pass for major frontend/backend flows.
  - One low-priority note about `/api/auth/google/start` behavior when redirects are followed.
- `/app/test_reports/iteration_3.json`
  - Auth regression retest passed 100%.
  - `/api/auth/google/start` now returns **proper 302 redirect**.

**Definition of Done (Phase 2):** Met.

---

### Phase 3 — Multi-site + Team Features + Background Jobs + Hardening (Next)
**Goal:** Expand from PMI single-site V1 to multi-site orgs, add team capabilities, automate runs, and improve operational robustness.

**Scope:**
- **Multi-site (per org)**
  - Add multiple sites, site switcher in UI, aggregated org dashboard
- **Team roles & permissions**
  - Invite teammates, role-based access (admin/manager/viewer)
- **Background jobs**
  - Scheduled daily signal fetch (weather/prices)
  - Nightly analysis run + alert generation
  - De-duplication of notifications
- **Email provider (production-grade)**
  - Replace dev-mode logging with Mailgun/SendGrid/SES
  - Template management + delivery retries + suppression
- **Object storage for PDFs**
  - Move from local storage to S3/R2/MinIO with presigned URLs
- **Observability & security hardening**
  - Structured logs, error tracking, audit events, rate limiting
  - Improved tenant isolation tests
- **PDF extraction improvements**
  - Better extraction library pipeline + field mapping UI

**User stories (Phase 3):**
1. As an org admin, I can add multiple sites and switch between them.
2. As an org admin, I can invite teammates and assign roles.
3. As a user, I receive scheduled daily/weekly email alerts reliably.
4. As a user, I can store and download bills from object storage securely.
5. As an admin, I can see job execution history and failures.

**Testing (Phase 3):**
- Multi-tenant + multi-site regression suite
- Scheduled jobs integration tests
- Email provider sandbox tests + retry/idempotency checks
- Load tests on dashboard/analytics endpoints

---

### Phase 4 — Advanced Optimization + Billing + Enterprise Readiness
**Scope:**
- Real feature gating (Free/Pro) + billing (Stripe)
- Advanced analytics/ML (weather normalization, more robust anomaly detection)
- Enterprise/public-sector readiness (audit logs, compliance posture)
- Smart-meter ingestion connectors and richer real-time workflows

---

## 3) Next Actions
1. Phase 3 discovery: confirm multi-site UX, role model, and scheduling requirements.
2. Select production email provider and implement real delivery.
3. Introduce object storage for bill PDFs and report PDFs.
4. Add background worker/scheduler (e.g., APScheduler/Celery) and job monitoring.
5. Improve PDF extraction quality + review workflow.
6. Prepare billing plan (Stripe) for Phase 4.

---

## 4) Success Criteria
- **Phase 1:** Completed: core workflow validated with real signals and POC endpoints.
- **Phase 2 (V1):** Completed:
  - Usable web app: login → onboarding → data ingestion → analytics → advices/ROI → prediction → report.
  - Google OAuth works (302 start + callback); dev/test bypass available only in non-production.
  - Weather and energy price signals integrated with caching/fallback.
  - Notifications working (in-app + dev-mode email logging).
  - Documentation shipped under `/app/docs`.
  - E2E testing validated in `/app/test_reports/iteration_2.json` and auth regression in `/app/test_reports/iteration_3.json`.
- **Phase 3+ target:** multi-site + teams + background automation + production email + object storage + advanced analytics and billing readiness.
