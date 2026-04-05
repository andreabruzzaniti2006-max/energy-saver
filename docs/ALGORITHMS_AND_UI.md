# Algorithms, Product Logic, and UI Mockup Notes

## Core Analytics Logic

### 1) Data ingestion
The app accepts two input modes:
- **PDF bill upload** with best-effort parsing of:
  - consumption kWh
  - total cost EUR
  - billing period
- **Manual readings** entered as single records or batch import

If no granular manual readings exist, parsed bills are converted into a daily average series to enable forecasting and reporting.

### 2) Weather enrichment
- Source: **OpenWeather**
- Used to capture current temperature context and influence forecast multipliers
- Cached locally to reduce repeated calls and stay within quota

### 3) Energy price enrichment
- Source: **Energy Charts** (`IT-North`)
- Input unit: EUR/MWh
- Internal normalized unit: **EUR/kWh**
- Hourly price profile is averaged by hour of day and applied to readings for cost estimation

### 4) Anomaly detection
V1 uses lightweight deterministic statistics:
- mean consumption baseline
- population standard deviation
- threshold = mean + max(1.6 * std, constant floor)
- extra checks for:
  - after-hours load
  - weekend overuse

This produces actionable anomalies without needing heavy ML infra.

### 5) Smart advice engine (core product)
Advice generation is rule-based and ROI-oriented:
- residual load after closing time
- high night baseload
- peak-time price shifting opportunity
- HVAC optimization when temperature is outside comfort band
- weekend waste control

Each advice includes:
- monthly savings estimate
- investment estimate
- payback months
- year-1 ROI %
- concrete next action

### 6) Cost prediction
Forecast is based on:
- recent historical daily cost trend
- current energy price profile
- weather multiplier from comfort delta

Output:
- next 30-day estimated cost
- expected variation vs baseline
- alert flag if increase exceeds threshold

## UI Mockup Description

### Login
- Split layout
- Left: headline, dev bypass, Google login
- Right: contextual industry image + trust/value blocks

### Onboarding
- 4-step wizard
  1. Company and sector
  2. Site, city, geo coordinates, business hours
  3. First data input (PDF/manual)
  4. Savings objective + summary

### Dashboard
- Left-aligned SaaS shell
- KPI row with 4 cards
- Main chart area for consumption/cost/forecast
- Priority advice area and anomaly list
- Integration status cards for weather, price, email mode, Google login

### Bills page
- Upload card on top
- Archive table below
- Review dialog for extracted fields

### Consumption page
- Single-entry form
- Batch import panel
- Readings history table

### Insights page
- Anomaly timeline with filters
- Advice cards with ROI/payback
- Forecast summary blocks

### Reports page
- Generate report CTA
- Report archive cards with download action

### Pricing page
- Free vs Pro comparison
- UI-only upgrade CTA

### Settings page
- Notification preferences
- Integration summary
- Dev-mode email test
- Logout
