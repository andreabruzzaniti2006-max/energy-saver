# Project Structure

```text
/app
├── backend/
│   ├── server.py                 # FastAPI API, auth, onboarding, analytics, bills, reports
│   ├── energy_core.py            # Core analytics engine, signal fetching, PDF-ready storage helpers
│   ├── uploads/                  # Secure local bill storage for V1
│   ├── reports/                  # Generated PDF reports
│   └── cache/                    # Cached weather/price responses
├── frontend/
│   └── src/
│       ├── App.js                # Router + auth guards
│       ├── App.css               # Minimal shared CSS
│       ├── index.css             # Global design tokens + typography
│       ├── lib/api.js            # API client + format helpers
│       ├── components/
│       │   ├── AppShell.jsx      # Sidebar/topbar layout
│       │   ├── KpiCard.jsx       # KPI cards
│       │   ├── AdviceCard.jsx    # ROI/payback action cards
│       │   ├── ChartsPanel.jsx   # Recharts dashboard graphs
│       │   └── NotificationsCenter.jsx
│       └── pages/
│           ├── LoginPage.jsx
│           ├── OnboardingPage.jsx
│           ├── DashboardPage.jsx
│           ├── BillsPage.jsx
│           ├── ConsumptionPage.jsx
│           ├── InsightsPage.jsx
│           ├── ReportsPage.jsx
│           ├── PricingPage.jsx
│           └── SettingsPage.jsx
├── scripts/
│   └── poc_core_flow.py          # Phase 1 isolated proof-of-concept script
├── docs/
│   ├── PROJECT_STRUCTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── API_ENDPOINTS.md
│   ├── ALGORITHMS_AND_UI.md
│   └── DEPLOY_AND_ROADMAP.md
└── memory/
    └── test_credentials.md       # Dev bypass credentials for testing
```

## Runtime Architecture
- **Frontend:** React SPA with protected routes and guided onboarding
- **Backend:** FastAPI with `/api/*` endpoints
- **Database:** MongoDB collections scoped by `org_id` and `site_id`
- **Real integrations:** OpenWeather, Energy Charts price API, Google OAuth
- **V1 storage:** secure local bill/report files, ready to move to object storage later
