# API Endpoints

## Auth
- `POST /api/auth/dev-login`
  - Dev/test bypass login
- `GET /api/auth/google/start`
  - Starts Google OAuth redirect flow
- `GET /api/auth/google/callback`
  - Handles Google callback, creates session cookie, redirects to frontend
- `GET /api/auth/me`
  - Returns authenticated session, org and site
- `POST /api/auth/logout`
  - Clears auth cookie

## Onboarding
- `GET /api/onboarding/state`
  - Returns current org/site setup
- `POST /api/onboarding/complete`
  - Saves company, sector, site, business hours and savings goal

## Bills
- `POST /api/bills/upload`
  - Upload PDF bill
  - `multipart/form-data` with `file`
- `GET /api/bills`
  - Lists bills for current site
- `GET /api/bills/{bill_id}`
  - Returns single bill detail
- `PATCH /api/bills/{bill_id}`
  - Manual correction of extracted fields

## Consumption
- `POST /api/consumption`
  - Create single reading
- `POST /api/consumption/batch`
  - Create multiple readings in one request
- `GET /api/consumption`
  - List readings
- `DELETE /api/consumption/{entry_id}`
  - Delete reading

## Analytics & Dashboard
- `POST /api/analytics/run`
  - Builds analysis from stored data, weather and price signals
- `GET /api/analytics/latest`
  - Returns latest analysis run for current site
- `GET /api/dashboard/overview`
  - Returns session, integration status, counts, latest analysis, recent bills, notifications

## Notifications
- `GET /api/notifications`
  - List notifications
- `POST /api/notifications/mark-all-read`
  - Marks unread notifications as read
- `GET /api/notifications/preferences`
  - Returns current preferences
- `POST /api/notifications/preferences`
  - Updates preferences
- `POST /api/notifications/test-email`
  - Logs a dev-mode email event

## Reports
- `POST /api/reports/generate`
  - Generates PDF report from latest analysis
- `GET /api/reports`
  - Lists generated reports
- `GET /api/reports/{report_id}/download`
  - Downloads PDF report

## POC / Regression-safe Core Endpoints
- `GET /api/poc/contracts`
- `POST /api/poc/ingest-manual`
- `POST /api/poc/upload-bill`
- `POST /api/poc/run-analysis`
- `GET /api/poc/latest-analysis`

## Utility
- `GET /api/health`
- `GET /api/status`
- `POST /api/status`
