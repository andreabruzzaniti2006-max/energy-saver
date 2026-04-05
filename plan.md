# Energy Optimization SaaS (React + FastAPI + Mongo) — Phased Plan

## 1) Objectives
- Deliver a sellable V1 SaaS for PMI (single site) that demonstrates **real economic impact** via: waste detection, smart advice w/ ROI, and cost prediction.
- Use current stack **React + FastAPI + MongoDB** while keeping SaaS-ready modularity (tenant/user isolation, roles, auditability).
- V1 requires real integrations: **Google OAuth**, **OpenWeather**, **energy price signal**, and **email notification flow** (development-mode is acceptable initially).
- **Approach:** De-risk analytics + integrations first via a POC, then build the full working app.

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
- POC endpoints available under `/api/poc/*`:
  - `GET /api/poc/contracts`
  - `POST /api/poc/ingest-manual`
  - `POST /api/poc/upload-bill`
  - `POST /api/poc/run-analysis`
  - `GET /api/poc/latest-analysis`

**Exit criteria:** Met.

---

### Phase 2 — V1 Working App (Full Frontend + Core SaaS Backend + Required Integrations)
**Goal:** Turn the validated POC into a usable V1 product: full SaaS UX for PMI single-site, with required integrations (Google OAuth, weather/prices enrichment, notifications incl. dev-mode email), and a backend structure scalable to multi-site later.

#### 2.1 Scope (what we build in V1)
**Frontend (React + Tailwind)**
- **Authentication**
  - Google OAuth login
  - Simple **dev/test bypass** for agent/browser testing (feature-flagged; disabled in production)
- **Onboarding flow (PMI-first, single-site)**
  1) Create org + site (single)
  2) Set site location (address → lat/lon) and business hours
  3) Add first data: upload PDF or manual entry
- **Core pages**
  - Dashboard: KPIs + trends + “Top actions” advice list + alerts
  - Bills: upload, list, details, extraction status (“parsed / needs review”)
  - Consumption: manual entry UI (hourly/daily/monthly import), data table, simple CSV import
  - Insights: anomalies timeline + advice detail view w/ ROI/payback + filtering
  - Reports: generate/download monthly PDF report
  - Pricing: Free/Pro plans UI (feature gating only, no billing)
  - Settings: site settings, alert preferences, integration status

**Backend (FastAPI + MongoDB)**
- Transition from POC collections to SaaS-friendly entities:
  - `users`, `orgs`, `sites` (single-site in V1 but model supports multi-site),
  - `bills`, `consumption_readings`, `analytics_runs`, `advices`, `alerts`, `notification_preferences`
- Core APIs (V1):
  - Auth: Google OAuth + dev bypass
  - Org/Site: create/read/update
  - Bills: upload/list/detail; extraction status and extracted fields
  - Consumption: create/list/import
  - Analytics: run analysis, get latest KPIs, list anomalies, list advices
  - Reports: generate + download PDF
  - Notifications:
    - in-app notifications (dashboard)
    - development-mode email notifications (log / internal emergent dev email mechanism)
- Integrations (V1):
  - Weather: OpenWeather (cached)
  - Prices: energy-charts (cached) + graceful fallback if unavailable

**Data & Analytics**
- Move `energy_core` logic into a service module (keep it deterministic + unit tested)
- Add persistence of:
  - analysis inputs/outputs
  - advice history
  - alert events and notification attempts
- Ensure all computations are tenant-scoped (org/site).

#### 2.2 User stories (Phase 2)
**Auth & onboarding**
1. As a user, I can sign in with Google and be redirected to my dashboard.
2. As a user (or tester), I can use a dev bypass login in non-production environments to access the app quickly.
3. As a user, I can complete onboarding (site location + hours + first data input) and reach a usable dashboard.

**Data ingestion**
4. As a user, I can upload a bill PDF and see it stored with extraction status and extracted fields.
5. As a user, if PDF extraction is incomplete, I can manually correct key fields (consumption, total cost, billing period).
6. As a user, I can enter consumption readings manually (hourly/daily/monthly) and edit them later.

**Analytics & value delivery**
7. As a user, I can run analysis and immediately see updated KPIs, anomalies, and prioritized savings actions.
8. As a user, I can open an advice detail view and see estimated monthly savings, investment, payback, and ROI.
9. As a user, I can see a 30-day cost forecast and an alert when expected cost increases above a threshold.

**Notifications & reporting**
10. As a user, I can see in-app alerts on the dashboard for anomalies and forecast warnings.
11. As a user, I can enable “email alerts” (dev-mode) and verify alerts are sent/logged.
12. As a user, I can generate and download a monthly PDF report summarizing KPIs, anomalies, and actions.

**Productization**
13. As a user, I can view Free/Pro plans and understand feature differences (no payment required in V1).

#### 2.3 Testing requirements (Phase 2)
**Backend**
- Integration tests:
  - Google OAuth callback flow (staging) + dev-bypass flow (local/preview)
  - Bills upload (valid/invalid, file size limit) + extraction status transitions
  - Consumption CRUD + CSV import
  - Analytics run persists correct entities (analysis_runs, advices, alerts)
  - External integrations contract tests:
    - OpenWeather: success + invalid key + rate limit handling
    - energy-charts: success + timeout/failure fallback
- Security tests:
  - Tenant scoping enforced on all queries (org/site)
  - File upload validation (MIME, size)

**Frontend**
- E2E tests (Playwright/Cypress style flows):
  - login (dev bypass) → onboarding → upload bill/manual entry → run analysis → see dashboard
  - advice details view shows ROI/payback
  - report generation downloads PDF
- UI tests:
  - empty states (no data) + error states (integration offline)

**Definition of Done (Phase 2)**
- A new user can: login → onboard → add data (manual or PDF) → run analysis → see KPIs/anomalies/advices → export report.
- Integrations are live and resilient (cached + fallback).
- Notifications are visible in-app; email path works in dev-mode.

---

### Phase 3 — Multi-site + Team Features + Hardening (Post-V1)
**Goal:** Expand from single-site PMI to multi-site orgs and more operational maturity.

**Scope:**
- Multi-site per org + aggregation views
- Roles/permissions + teammate invites
- Scheduled jobs (nightly analysis, daily signals refresh)
- Observability (structured logging, error tracking), data retention policies
- Improved PDF extraction pipeline and field mapping UI

**User stories (Phase 3):**
1. As an org admin, I can add multiple sites and view aggregated KPIs.
2. As an org admin, I can invite teammates and assign roles.
3. As a user, I can see site comparisons and rank waste and savings potential.

**Testing:**
- Multi-tenant + multi-site regression
- Load tests on dashboard + analytics endpoints

---

### Phase 4 — Advanced Optimization + Billing + Enterprise Readiness
**Scope:**
- Feature gating enforcement (Free/Pro) + real billing (Stripe)
- Advanced ML models (weather-normalized demand modeling, robust anomaly detection)
- Public sector/enterprise readiness (audit logs, compliance posture)
- Hardware/smart-meter ingestion connectors

---

## 3) Next Actions
1. **Lock V1 information architecture + UX flows** (onboarding, dashboard, bills, insights, reports, pricing).
2. Refactor POC modules into production-ready services (keep POC endpoints for regression/demo).
3. Implement Google OAuth + dev/test bypass.
4. Implement core SaaS data model + tenant scoping (org/site), single-site UI default.
5. Build UI pages + wire up APIs end-to-end.
6. Add dev-mode email notifications + in-app notifications.
7. Add report generation (PDF) + download.
8. Execute Phase 2 E2E tests in preview environment.

---

## 4) Success Criteria
- **Phase 1:** Completed: core workflow validated with real signals and POC endpoints.
- **Phase 2 (V1):**
  - Usable web app: login → onboarding → data ingestion → analytics → advices/ROI → prediction → report.
  - Google OAuth works; dev/test bypass available only in non-production.
  - Weather and energy price signals integrated with caching/fallback.
  - Notifications working (in-app + dev-mode email).
  - Architecture remains SaaS-ready and scalable to multi-site in later phases.