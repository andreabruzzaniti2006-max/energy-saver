# Here are your Instructions

Energy Saver SaaS
Software SaaS per l’ottimizzazione dei consumi energetici pensato per PMI come bar, ristoranti e palestre, con struttura già predisposta per evolvere verso scenari multi-sede e utilizzo anche da parte di realtà più grandi.

L’obiettivo del progetto è trasformare i dati energetici in azioni concrete, mostrando:

dove si stanno generando sprechi,
quanto stanno costando,
quali interventi conviene fare per primi,
quale risparmio economico è realisticamente ottenibile.
Panoramica
Energy Saver aiuta aziende e attività commerciali a:

monitorare consumi e costi energetici,
caricare bollette PDF o inserire consumi manualmente,
rilevare anomalie,
ricevere suggerimenti smart con ROI e tempo di rientro,
visualizzare una previsione dei costi futuri,
generare report PDF pronti da condividere.
Il sistema è stato progettato con un approccio pratico: massimo impatto economico, minima complessità operativa.

Funzionalità principali
1. Dashboard intelligente
KPI principali:
costo energia,
consumo totale,
sprechi stimati,
risparmio potenziale.
grafici giornalieri dei consumi e dei costi,
forecast dei costi futuri,
stato integrazioni (meteo, prezzi energia, auth, notifiche).
2. Upload bollette PDF
caricamento bollette PDF,
parsing best-effort dei dati principali,
stato documento:
parsed
needs_manual_review
revisione manuale dei campi estratti:
consumo kWh,
costo totale,
periodo bolletta.
3. Inserimento consumi manuale
inserimento singolo,
import batch rapido,
storico letture,
cancellazione voci errate.
4. Analisi automatica
rilevamento anomalie di consumo,
identificazione di carichi fuori orario,
evidenza di sprechi e picchi non coerenti con il profilo atteso.
5. Consigli smart
Per ogni azione suggerita il sistema mostra:

risparmio mensile stimato,
investimento stimato,
payback,
ROI del primo anno,
azione operativa consigliata.
6. Predizione costi
Stima dei costi energetici futuri sulla base di:

storico consumi,
prezzi energia,
contesto meteo.
7. Notifiche
notifiche in-app,
preferenze personalizzabili,
test email in modalità sviluppo.
8. Report PDF
generazione report mensili,
riepilogo KPI,
sprechi rilevati,
opportunità di risparmio,
download PDF.
9. Autenticazione
Google OAuth,
dev bypass login per test e demo in ambiente non production.
10. Pricing UI
piano Free,
piano Pro,
interfaccia pronta per billing futuro.
Come funziona
Flusso utente
Login

accesso con Google oppure login demo/dev.
Onboarding

inserimento azienda,
configurazione sede,
città e coordinate,
orari di apertura,
obiettivo di risparmio.
Inserimento dati

caricamento PDF bolletta,
oppure inserimento manuale dei consumi.
Revisione bollette

se il PDF non viene interpretato completamente, la bolletta passa in stato needs_manual_review,
l’utente può completare manualmente i campi mancanti.
Analisi

il backend combina:
dati consumo,
meteo reale,
prezzi energia,
genera KPI, anomalie, suggerimenti e forecast.
Visualizzazione risultati

dashboard con grafici e KPI,
insights con timeline anomalie,
consigli prioritari con ROI.
Report e notifiche

generazione report PDF,
notifiche sugli eventi più rilevanti.
Logica di analisi
Il motore di analisi utilizza una logica deterministica e leggera, ideale per una V1 SaaS:

Anomaly Detection
Basata su:

media storica,
deviazione standard,
controllo carichi fuori orario,
uso anomalo nei weekend.
Advice Engine
Sistema rule-based che genera consigli come:

spegnimento carichi residui,
riduzione baseload notturno,
spostamento consumi fuori fascia di picco,
ottimizzazione HVAC.
Cost Prediction
La previsione combina:

andamento storico,
prezzo energia,
impatto termico/meteo.
Stack tecnologico
Frontend
React
TailwindCSS
shadcn/ui
Recharts
Backend
FastAPI
MongoDB
JWT session cookies
Integrazioni
OpenWeather
Energy Charts API
Google OAuth
Struttura del progetto
/app
├── backend/
│   ├── server.py
│   ├── energy_core.py
│   ├── uploads/
│   ├── reports/
│   └── cache/
├── frontend/
│   └── src/
│       ├── App.js
│       ├── index.css
│       ├── lib/
│       ├── components/
│       └── pages/
├── scripts/
│   └── poc_core_flow.py
├── docs/
│   ├── PROJECT_STRUCTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── API_ENDPOINTS.md
│   ├── ALGORITHMS_AND_UI.md
│   └── DEPLOY_AND_ROADMAP.md
└── memory/
    └── test_credentials.md
Avvio del progetto
Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
Frontend
cd frontend
yarn install
yarn start
Variabili ambiente
Backend
MONGO_URL=
DB_NAME=
CORS_ORIGINS=

OPENWEATHER_API_KEY=
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5/weather

ENERGY_PRICE_API_URL=https://api.energy-charts.info/price?bzn=IT-North

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
FRONTEND_APP_URL=

JWT_SECRET=

EMAIL_DELIVERY_MODE=emergent-dev
FILE_STORAGE_MODE=local_secure
APP_ENV=development
Frontend
REACT_APP_BACKEND_URL=
REACT_APP_GOOGLE_CLIENT_ID=
Endpoint principali
Auth
POST /api/auth/dev-login
GET /api/auth/google/start
GET /api/auth/google/callback
GET /api/auth/me
POST /api/auth/logout
Onboarding
GET /api/onboarding/state
POST /api/onboarding/complete
Bills
POST /api/bills/upload
GET /api/bills
GET /api/bills/{bill_id}
PATCH /api/bills/{bill_id}
Consumption
POST /api/consumption
POST /api/consumption/batch
GET /api/consumption
DELETE /api/consumption/{entry_id}
Analytics
POST /api/analytics/run
GET /api/analytics/latest
GET /api/dashboard/overview
Notifications
GET /api/notifications
POST /api/notifications/mark-all-read
GET /api/notifications/preferences
POST /api/notifications/preferences
POST /api/notifications/test-email
Reports
POST /api/reports/generate
GET /api/reports
GET /api/reports/{report_id}/download
Note importanti
Le bollette PDF in stato needs_manual_review vengono escluse dall’analisi finché i campi essenziali non vengono completati.
Le notifiche email sono attualmente in modalità sviluppo.
Il piano Pro è attualmente solo UI, senza billing reale attivo.
Il sistema è ottimizzato per single-site V1, ma la struttura backend è già predisposta per multi-sede.
Stato del progetto
Completato
POC core validato
onboarding guidato
dashboard SaaS completa
upload bollette + review
consumi manuali
analisi + anomaly detection
consigli con ROI
forecast costi
notifiche in-app
report PDF
Google OAuth + dev bypass
documentazione tecnica
Prossimi sviluppi
multi-sede
ruoli e team
scheduler automatico
email provider reale
object storage
billing Stripe
modelli predittivi più avanzati
Roadmap
Fase successiva
multi-account / multi-sede,
ruoli utenti,
automazione analisi periodiche,
email provider production-ready,
storage file su S3 / R2 / MinIO.
Evoluzione futura
billing Pro,
benchmarking tra sedi,
ML avanzato,
connettori smart meter / IoT,
funzioni enterprise / enti pubblici.
Obiettivo del prodotto
Energy Saver è pensato per essere un prodotto:

semplice da usare,
utile fin dal primo giorno,
vendibile come SaaS,
focalizzato sul risparmio economico reale.
