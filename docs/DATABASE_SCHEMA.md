# Database Schema (MongoDB V1)

> Note: the original request mentioned PostgreSQL. The user approved building V1 on the current stack **React + FastAPI + MongoDB**. This schema preserves SaaS structure and can be mapped later to PostgreSQL if needed.

## Core Collections

### `users`
```json
{
  "_id": "ObjectId",
  "email": "user@example.com",
  "name": "Mario Rossi",
  "provider": "google | dev-bypass",
  "google_id": "optional-google-sub",
  "org_id": "string:ObjectId",
  "site_id": "string:ObjectId",
  "created_at": "datetime"
}
```

### `orgs`
```json
{
  "_id": "ObjectId",
  "name": "Bar Milano Centro SRL",
  "plan": "free | pro",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `sites`
```json
{
  "_id": "ObjectId",
  "org_id": "string:ObjectId",
  "name": "Sede principale",
  "city": "Milano",
  "latitude": 45.4642,
  "longitude": 9.19,
  "business_open_hour": 6,
  "business_close_hour": 19,
  "sector": "bar | ristorante | palestra | altro",
  "savings_goal_pct": 15,
  "onboarding_completed": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `bills`
```json
{
  "_id": "ObjectId",
  "user_id": "string:ObjectId",
  "org_id": "string:ObjectId",
  "site_id": "string:ObjectId",
  "filename": "bill-april.pdf",
  "storage_mode": "local_secure",
  "relative_path": "uploads/...pdf",
  "size_bytes": 42812,
  "uploaded_at": "datetime",
  "extraction_status": "parsed | needs_manual_review | invalid_pdf",
  "notes": "optional",
  "extracted_fields": {
    "consumption_kwh": 980.0,
    "total_cost_eur": 241.9,
    "period_start": "01/03/2026",
    "period_end": "31/03/2026",
    "raw_text_preview": "..."
  }
}
```

### `consumption_readings`
```json
{
  "_id": "ObjectId",
  "user_id": "string:ObjectId",
  "org_id": "string:ObjectId",
  "site_id": "string:ObjectId",
  "timestamp": "datetime",
  "kwh": 12.4,
  "cost_eur": 3.18,
  "note": "apertura",
  "created_at": "datetime"
}
```

### `analytics_runs`
```json
{
  "_id": "ObjectId",
  "user_id": "string:ObjectId",
  "org_id": "string:ObjectId",
  "site_id": "string:ObjectId",
  "created_at": "datetime",
  "weather_context": { "status": "ok", "temperature_c": 14 },
  "price_signal_summary": { "status": "ok", "source": "energy-charts", "items_count": 96 },
  "analysis": {
    "kpis": {
      "total_consumption_kwh": 1200.0,
      "total_cost_eur": 340.0,
      "estimated_waste_eur": 28.0,
      "potential_monthly_savings_eur": 85.0
    },
    "anomalies": [],
    "advices": [],
    "prediction": {}
  }
}
```

### `notifications`
```json
{
  "_id": "ObjectId",
  "user_id": "string:ObjectId",
  "org_id": "string:ObjectId",
  "site_id": "string:ObjectId",
  "type": "anomaly | forecast | savings",
  "severity": "low | medium | high",
  "title": "Anomalia di consumo rilevata",
  "message": "...",
  "read": false,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `notification_preferences`
```json
{
  "_id": "ObjectId",
  "user_id": "string:ObjectId",
  "org_id": "string:ObjectId",
  "site_id": "string:ObjectId",
  "email_enabled": false,
  "anomaly_alerts": true,
  "price_alerts": true,
  "report_alerts": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `notification_events`
```json
{
  "_id": "ObjectId",
  "user_id": "string:ObjectId",
  "org_id": "string:ObjectId",
  "site_id": "string:ObjectId",
  "mode": "emergent-dev",
  "status": "logged",
  "event_type": "analysis_summary | manual_test",
  "payload": {},
  "created_at": "datetime"
}
```

### `reports`
```json
{
  "_id": "ObjectId",
  "user_id": "string:ObjectId",
  "org_id": "string:ObjectId",
  "site_id": "string:ObjectId",
  "filename": "report-...pdf",
  "relative_path": "reports/report-...pdf",
  "download_path": "/api/reports/{id}/download",
  "summary": {
    "potential_monthly_savings_eur": 85.0,
    "estimated_waste_eur": 28.0
  },
  "created_at": "datetime"
}
```

## Multi-tenant Rules
- Every business entity is filtered by `org_id`
- Every operational dataset is filtered by `site_id`
- V1 UI is single-site, but the backend schema is already compatible with future multi-site expansion
