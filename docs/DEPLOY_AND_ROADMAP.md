# Deploy Steps and Future Roadmap

## Deployment (current architecture)

### Frontend
Recommended targets:
- Vercel
- Railway static service
- Render static web service

Required env:
- `REACT_APP_BACKEND_URL=https://your-domain.com`
- `REACT_APP_GOOGLE_CLIENT_ID=...`

Build command:
```bash
yarn build
```

### Backend
Recommended targets:
- Railway
- Render
- Fly.io

Required env:
- `MONGO_URL=...`
- `DB_NAME=...`
- `CORS_ORIGINS=https://your-frontend-domain.com`
- `OPENWEATHER_API_KEY=...`
- `OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5/weather`
- `ENERGY_PRICE_API_URL=https://api.energy-charts.info/price?bzn=IT-North`
- `GOOGLE_CLIENT_ID=...`
- `GOOGLE_CLIENT_SECRET=...`
- `GOOGLE_REDIRECT_URI=https://your-domain.com/api/auth/google/callback`
- `FRONTEND_APP_URL=https://your-domain.com`
- `JWT_SECRET=strong-32+-char-secret`
- `EMAIL_DELIVERY_MODE=emergent-dev` (or replace with real provider later)
- `FILE_STORAGE_MODE=local_secure`

Start command:
```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8001
```

> In the current managed environment, supervisor already starts the backend automatically.

### Google OAuth checklist
1. Create credentials in Google Cloud Console
2. Add authorized redirect URI:
   - `https://your-domain.com/api/auth/google/callback`
3. Add JavaScript origins for frontend domain if needed
4. Test login in preview/staging

### MongoDB
- For production use MongoDB Atlas or managed Mongo
- Create a dedicated database
- Restrict network access and use strong credentials

### Files and reports
V1 uses secure local storage for bills and generated reports.
For production scale, move to object storage:
- AWS S3
- Cloudflare R2
- MinIO

## Future Roadmap

### Phase 3
- Multi-site per organization
- Role-based access / team invites
- Scheduled nightly analyses
- Better extraction review workflow
- Improved observability and audit trail

### Phase 4
- Real billing (Stripe)
- Advanced ML models
- Smart-meter / IoT connectors
- Public-sector reporting templates
- Advanced benchmarking across sites

### Phase 5
- Procurement-grade reporting
- Advanced recommendation personalization
- Portfolio-level optimization for multi-location enterprises
