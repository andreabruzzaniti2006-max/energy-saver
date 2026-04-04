# Energy Optimization SaaS (React + FastAPI + Mongo) — Phased Plan

## 1) Objectives
- Deliver a sellable V1 SaaS for PMI (single site) that demonstrates **real economic impact** via: waste detection, smart advice w/ ROI, and cost prediction.
- Use current stack **React + FastAPI + MongoDB** while keeping SaaS-ready modularity (tenant/user isolation, roles, auditability).
- V1 requires real integrations: **Google OAuth**, **OpenWeather**, **energy price signal**, **email notifications**.
- **Decision:** Phase 1 WILL be a POC isolation phase (core workflow includes multiple external integrations + file/PDF ingestion + analytics → high failure risk). Do not proceed to full app until POC passes success criteria.

---

## 2) Implementation Steps

### Phase 1 — Core Workflow POC (Isolation) 
**Goal:** Prove end-to-end core logic works with real inputs and integrations, via scripts + minimal API.

**Scope (POC):**
- Ingest energy data from: (1) manual entry (CSV-like payload) and (2) **PDF-ready upload flow** (store file + stub extraction OR basic extraction if feasible).
- Fetch **weather** (OpenWeather) and **price signal** (choose a source; if no official API, use a stable public endpoint + caching + fallback manual tariff table).
- Run:
  - anomaly detection (simple seasonal baseline + z-score / rolling stats)
  - smart advice (rule-based patterns + estimated savings)
  - ROI estimation (savings − cost; payback)
  - cost prediction (baseline regression vs degree-days + price)
- Validate integration strategy: secrets, rate limits, retries, caching, and data contracts.
- Websearch task (during POC): confirm best practice for (a) OpenWeather usage/caching, (b) Italy/EU price signal sources, (c) PDF extraction approach (pdfplumber/tabula/textract) and accuracy tradeoffs.

**User stories (POC):**
1. As a user, I can upload a bill PDF and see it stored with metadata so I can start analysis immediately.
2. As a user, I can paste/submit manual monthly consumption and cost data to bootstrap insights.
3. As a user, I can run an “Analyze now” job and get anomalies detected on my sample dataset.
4. As a user, I can see 3–5 actionable advices with savings €/month and ROI so I can decide what to do.
5. As a user, I can see next-month cost prediction and an alert when forecasted cost rises above threshold.

**Testing (POC):**
- Contract tests for external APIs (happy path + rate limit + missing fields).
- Golden dataset tests: given a small fixed timeseries → anomalies + advice output stable.
- PDF pipeline test: upload → stored → parsed fields OR “needs manual mapping” state.
- Determinism: analytics functions pure + unit tested.

**Deliverables:**
- `/scripts/poc_core_flow.py` that runs: ingest sample → fetch signals → analytics → prints JSON report.
- Minimal FastAPI endpoints: `/poc/upload-bill`, `/poc/ingest-manual`, `/poc/run-analysis`.
- Documented data contracts (JSON schemas) for consumption, weather, prices, analytics outputs.

**Exit criteria:**
- One real OpenWeather call succeeds and is cached.
- One real price signal call succeeds OR documented fallback works.
- POC generates consistent anomalies + advice + ROI + prediction on sample data.

---

### Phase 2 — V1 App Development (MVP, no billing, delay auth until Phase 3)
**Goal:** Build the product around the proven core. Keep multi-site scalable but UI targets single site.

**App structure guidance (monorepo):**
- `/frontend` React + Tailwind: pages (Dashboard, Bills, Insights, Reports, Settings)
- `/backend` FastAPI: routers (auth placeholder, org/site, bills, consumption, analytics, notifications, integrations)
- `/shared` JSON schemas (Pydantic models mirrored as TS types via codegen or manual)

**Backend scope:**
- Entities in Mongo (collections):
  - `users`, `orgs`, `sites`(single in V1), `bills`, `consumption_readings`(daily/monthly), `analytics_runs`, `advices`, `alerts`, `integrations_state`
- Job execution: synchronous for MVP; keep interface ready for async worker later.
- APIs:
  - Bills: upload, list, view, extraction status
  - Consumption: manual create/edit, import CSV, list
  - Analytics: run, get latest KPIs, list advices, list anomalies
  - Notifications: create alert rules, list events

**Frontend scope (UX):**
- Onboarding wizard (3 steps): create org/site → add tariff basics → add first data (manual or PDF upload).
- Dashboard: KPI cards + charts + “Top 5 actions” advice list.
- Bills page: upload + table + “needs review” extraction.
- Insights page: anomalies timeline + filters; advice detail view with ROI.
- Pricing page (Free/Pro) with feature gating UI only.

**User stories (V1):**
1. As a user, I can complete onboarding and see a demo dashboard even before full data is available.
2. As a user, I can upload bills and track their extraction/review status.
3. As a user, I can enter consumption/cost data and immediately refresh KPIs.
4. As a user, I can receive in-app alerts for anomalies and forecasted bill increases.
5. As a user, I can export a monthly PDF report to share with my accountant/manager.

**Testing (V1):**
- E2E: onboarding → add data → run analysis → see dashboard → export report.
- API integration tests for file upload + analytics run.
- Frontend component tests for charts/cards and empty/error states.

**Exit criteria:**
- End-to-end workflow works without auth: onboarding → ingest → analyze → advice/prediction visible.
- Report PDF generated and downloadable.

---

### Phase 3 — Integrations + Auth + Notifications (Production readiness)
**Goal:** Add real-world access control + required integrations (Google login, email) and harden.

**Scope:**
- Google OAuth (Authorization Code flow) + JWT session tokens.
- Tenant isolation: org_id enforced on every query.
- Email notifications: SendGrid/Mailgun/SMTP; templates for anomalies/forecast/advice.
- Background scheduling (simple cron): daily fetch weather/prices; nightly analysis run.

**User stories (Phase 3):**
1. As a user, I can sign in with Google and return to my organization dashboard.
2. As an admin, I can invite a teammate and control access to insights and reports.
3. As a user, I can enable email alerts and choose threshold preferences.
4. As a user, I can see an audit trail of analysis runs and alerts sent.
5. As a user, I can recover access securely (logout everywhere / token expiry).

**Testing (Phase 3):**
- OAuth E2E in staging (redirect URIs, state/nonce, token refresh).
- Email sandbox tests + deliverability checks.
- Security tests: auth-required routes, org isolation, file upload validation.

**Exit criteria:**
- Google login works in staging + production.
- Emails sent reliably with retries and suppression of duplicates.

---

### Phase 4 — Scale features (multi-site, pricing gates, advanced analytics)
**Scope:**
- Multi-site per org (UI + aggregation) while keeping PMI-first UX.
- Feature gating for Free/Pro (still no payments) + usage limits.
- Improved models: better baselines, weather normalization, more robust anomaly detection.
- Admin console + observability (logs/metrics), data retention policies.

**User stories (Phase 4):**
1. As a user, I can add a second site and view an aggregated org dashboard.
2. As a user, I can compare sites and identify which has the highest waste.
3. As a Pro user, I can access advanced predictions and full reports.
4. As an admin, I can monitor system health and failed integrations.
5. As a user, I can download historical reports and benchmarks.

**Testing (Phase 4):**
- Multi-tenant + multi-site regression tests.
- Load test core endpoints (dashboard, analytics run).

---

## 3) Next Actions
1. Collect required credentials/secrets: OpenWeather key, price API source/key (or confirm fallback), Google OAuth client + redirect URIs, email provider SMTP/API key.
2. Approve POC approach for PDF: store + parse best-effort + manual review fallback.
3. Implement Phase 1 scripts + minimal FastAPI endpoints; run with real sample bills/inputs.
4. Freeze schemas for: consumption input, analytics output, advice model.

---

## 4) Success Criteria
- POC proves: manual + PDF-ready ingestion → weather/price enrichment → anomaly + advice/ROI + prediction outputs are correct enough to demo.
- V1 delivers: onboarding + dashboard + insights + bill management + PDF report with stable UX.
- Integrations deliver: Google login + email alerts working in staging/prod.
- System is SaaS-ready: org isolation, modular services, deployable with documented steps.
