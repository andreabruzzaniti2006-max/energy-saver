from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
import logging
import os
import uuid

import jwt
import requests
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import APIRouter, Cookie, Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from starlette.middleware.cors import CORSMiddleware

from energy_core import (
    DEFAULT_CITY,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    analyze_dataset,
    build_contract_examples,
    build_sample_readings,
    fetch_energy_prices,
    fetch_weather_context,
    parse_dt,
    store_bill_file,
    to_iso,
)

ROOT_DIR = Path(__file__).parent
REPORTS_DIR = ROOT_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

APP_ENV = os.getenv("APP_ENV", "development")
SESSION_COOKIE_NAME = "energy_session"
JWT_SECRET = os.getenv("JWT_SECRET", "energy-saver-dev-jwt-secret-2026-long-key")
JWT_ALGORITHM = "HS256"
EMAIL_DELIVERY_MODE = os.getenv("EMAIL_DELIVERY_MODE", "emergent-dev")
FRONTEND_APP_URL = os.getenv("FRONTEND_APP_URL", "https://energy-saver-16.preview.emergentagent.com")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Energy Saver SaaS API", version="1.0.0")
api_router = APIRouter(prefix="/api")


class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


class DevLoginRequest(BaseModel):
    email: EmailStr = "demo@energysaver.app"
    name: str = "Energy Saver Demo"
    company_name: str = "Energy Saver Demo"


class ManualReading(BaseModel):
    timestamp: datetime
    kwh: float
    cost_eur: Optional[float] = None


class ManualIngestRequest(BaseModel):
    site_name: str = "PMI Demo Site"
    city: str = DEFAULT_CITY
    latitude: float = DEFAULT_LATITUDE
    longitude: float = DEFAULT_LONGITUDE
    readings: Optional[List[ManualReading]] = None


class AnalysisRequest(BaseModel):
    site_name: str = "PMI Demo Site"
    city: str = DEFAULT_CITY
    latitude: float = DEFAULT_LATITUDE
    longitude: float = DEFAULT_LONGITUDE
    dataset_id: Optional[str] = None
    readings: Optional[List[ManualReading]] = None


class StoredDocumentResponse(BaseModel):
    id: str
    created_at: str
    payload: Dict[str, Any]


class OnboardingRequest(BaseModel):
    company_name: str
    sector: str
    site_name: str
    city: str
    latitude: float
    longitude: float
    business_open_hour: int
    business_close_hour: int
    savings_goal_pct: int = 12


class ConsumptionEntryCreate(BaseModel):
    timestamp: datetime
    kwh: float
    cost_eur: Optional[float] = None
    note: Optional[str] = None


class ConsumptionBatchRequest(BaseModel):
    entries: List[ConsumptionEntryCreate]


class NotificationPreferencesPayload(BaseModel):
    email_enabled: bool = False
    anomaly_alerts: bool = True
    price_alerts: bool = True
    report_alerts: bool = True


class BillReviewPayload(BaseModel):
    consumption_kwh: Optional[float] = None
    total_cost_eur: Optional[float] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    notes: Optional[str] = None


class AuthContext(BaseModel):
    user: Dict[str, Any]
    org: Dict[str, Any]
    site: Dict[str, Any]
    token_payload: Dict[str, Any]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def serialize_value(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return to_iso(value)
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_value(item) for key, item in value.items()}
    return value


def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    serialized = serialize_value(doc)
    if "_id" in serialized:
        serialized["id"] = serialized.pop("_id")
    return serialized


def to_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail="Identificativo non valido")
    return ObjectId(value)


def create_session_token(user_id: str, org_id: str, site_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "org_id": org_id,
        "site_id": site_id,
        "email": email,
        "iat": utc_now(),
        "exp": utc_now() + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Sessione scaduta") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Sessione non valida") from exc


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=APP_ENV == "production",
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


def build_google_state(next_path: str = "/dashboard") -> str:
    return jwt.encode(
        {
            "next_path": next_path,
            "iat": utc_now(),
            "exp": utc_now() + timedelta(minutes=10),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_google_state(state: str) -> Dict[str, Any]:
    try:
        return jwt.decode(state, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return {"next_path": "/dashboard"}


def parse_bill_period_date(value: Optional[str], fallback: datetime) -> datetime:
    if not value:
        return fallback
    try:
        return datetime.strptime(value, "%d/%m/%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            return parse_dt(value)
        except Exception:
            return fallback


def build_session_payload(user: Dict[str, Any], org: Dict[str, Any], site: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "user": {
            "id": str(user["_id"]),
            "email": user.get("email"),
            "name": user.get("name"),
            "provider": user.get("provider"),
        },
        "org": {
            "id": str(org["_id"]),
            "name": org.get("name"),
            "plan": org.get("plan", "free"),
        },
        "site": {
            "id": str(site["_id"]),
            "name": site.get("name"),
            "city": site.get("city"),
            "latitude": site.get("latitude"),
            "longitude": site.get("longitude"),
            "business_open_hour": site.get("business_open_hour"),
            "business_close_hour": site.get("business_close_hour"),
            "sector": site.get("sector"),
            "onboarding_completed": site.get("onboarding_completed", False),
        },
    }


async def ensure_preferences(user_id: str, org_id: str, site_id: str) -> Dict[str, Any]:
    existing = await db.notification_preferences.find_one({"user_id": user_id, "site_id": site_id})
    if existing:
        return existing
    doc = {
        "user_id": user_id,
        "org_id": org_id,
        "site_id": site_id,
        "email_enabled": False,
        "anomaly_alerts": True,
        "price_alerts": True,
        "report_alerts": True,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    result = await db.notification_preferences.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def bootstrap_user(email: str, name: str, provider: str, google_id: Optional[str] = None, company_name: Optional[str] = None):
    user = await db.users.find_one({"email": email})
    if not user:
        org_doc = {
            "name": company_name or f"{name.split(' ')[0]} Energy",
            "plan": "free",
            "created_at": utc_now(),
        }
        org_result = await db.orgs.insert_one(org_doc)
        site_doc = {
            "org_id": str(org_result.inserted_id),
            "name": "Sede principale",
            "city": DEFAULT_CITY,
            "latitude": DEFAULT_LATITUDE,
            "longitude": DEFAULT_LONGITUDE,
            "business_open_hour": 6,
            "business_close_hour": 18,
            "sector": "bar",
            "savings_goal_pct": 12,
            "onboarding_completed": False,
            "created_at": utc_now(),
        }
        site_result = await db.sites.insert_one(site_doc)
        user_doc = {
            "email": email,
            "name": name,
            "provider": provider,
            "google_id": google_id,
            "org_id": str(org_result.inserted_id),
            "site_id": str(site_result.inserted_id),
            "created_at": utc_now(),
        }
        user_result = await db.users.insert_one(user_doc)
        user = await db.users.find_one({"_id": user_result.inserted_id})
        org = await db.orgs.find_one({"_id": org_result.inserted_id})
        site = await db.sites.find_one({"_id": site_result.inserted_id})
    else:
        org = await db.orgs.find_one({"_id": to_object_id(user["org_id"])})
        site = await db.sites.find_one({"_id": to_object_id(user["site_id"])})
        update_fields: Dict[str, Any] = {}
        if google_id and not user.get("google_id"):
            update_fields["google_id"] = google_id
        if provider != user.get("provider"):
            update_fields["provider"] = provider
        if update_fields:
            await db.users.update_one({"_id": user["_id"]}, {"$set": update_fields})
            user.update(update_fields)
    await ensure_preferences(str(user["_id"]), str(org["_id"]), str(site["_id"]))
    return user, org, site


async def get_auth_context(energy_session: Optional[str] = Cookie(default=None)) -> AuthContext:
    if not energy_session:
        raise HTTPException(status_code=401, detail="Autenticazione richiesta")
    payload = decode_session_token(energy_session)
    user = await db.users.find_one({"_id": to_object_id(payload["sub"])})
    if not user:
        raise HTTPException(status_code=401, detail="Utente non trovato")
    org = await db.orgs.find_one({"_id": to_object_id(payload["org_id"])})
    site = await db.sites.find_one({"_id": to_object_id(payload["site_id"])})
    if not org or not site:
        raise HTTPException(status_code=401, detail="Contesto organizzativo non valido")
    return AuthContext(
        user=serialize_doc(user),
        org=serialize_doc(org),
        site=serialize_doc(site),
        token_payload=payload,
    )


def get_google_auth_url(next_path: str = "/dashboard") -> str:
    state = build_google_state(next_path)
    params = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "include_granted_scopes": "true",
        "prompt": "select_account",
        "state": state,
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_google_code(code: str) -> Dict[str, Any]:
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Scambio token Google fallito")
    return response.json()


def fetch_google_userinfo(access_token: str) -> Dict[str, Any]:
    response = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Recupero profilo Google fallito")
    return response.json()


async def gather_site_readings(site_id: str) -> List[Dict[str, Any]]:
    manual = await db.consumption_readings.find({"site_id": site_id}).sort("timestamp", 1).to_list(3000)
    if manual:
        return [
            {
                "timestamp": to_iso(parse_dt(item["timestamp"])),
                "kwh": float(item["kwh"]),
                "cost_eur": float(item["cost_eur"]) if item.get("cost_eur") is not None else None,
            }
            for item in manual
        ]

    bills = await db.bills.find({"site_id": site_id}).sort("uploaded_at", 1).to_list(200)
    expanded: List[Dict[str, Any]] = []
    for bill in bills:
        fields = bill.get("extracted_fields", {})
        consumption = fields.get("consumption_kwh")
        total_cost = fields.get("total_cost_eur")
        if consumption is None:
            continue
        uploaded_at = parse_dt(bill.get("uploaded_at") or utc_now())
        start_date = parse_bill_period_date(fields.get("period_start"), uploaded_at - timedelta(days=29))
        end_date = parse_bill_period_date(fields.get("period_end"), uploaded_at)
        days = max(1, (end_date.date() - start_date.date()).days + 1)
        daily_kwh = float(consumption) / days
        daily_cost = float(total_cost) / days if total_cost is not None else None
        for offset in range(days):
            moment = (start_date + timedelta(days=offset)).replace(hour=12, minute=0, second=0, microsecond=0)
            expanded.append(
                {
                    "timestamp": to_iso(moment),
                    "kwh": round(daily_kwh, 2),
                    "cost_eur": round(daily_cost, 2) if daily_cost is not None else None,
                }
            )
    return expanded


async def latest_analysis_for_site(site_id: str) -> Optional[Dict[str, Any]]:
    items = await db.analytics_runs.find({"site_id": site_id}).sort("created_at", -1).limit(1).to_list(1)
    return items[0] if items else None


async def create_notifications_from_analysis(ctx: AuthContext, analysis_doc: Dict[str, Any]) -> None:
    analysis = analysis_doc.get("analysis", {})
    preferences = await ensure_preferences(ctx.user["id"], ctx.org["id"], ctx.site["id"])
    notifications: List[Dict[str, Any]] = []
    for anomaly in (analysis.get("anomalies") or [])[:3]:
        if not preferences.get("anomaly_alerts", True):
            continue
        notifications.append(
            {
                "user_id": ctx.user["id"],
                "org_id": ctx.org["id"],
                "site_id": ctx.site["id"],
                "type": "anomaly",
                "severity": "high" if anomaly.get("estimated_loss_eur", 0) >= 0.5 else "medium",
                "title": "Anomalia di consumo rilevata",
                "message": f"{anomaly.get('reasons', ['Anomalia'])[0]} · impatto stimato EUR {anomaly.get('estimated_loss_eur', 0):.2f}",
                "read": False,
                "created_at": utc_now(),
            }
        )
    if analysis.get("prediction", {}).get("alert") and preferences.get("price_alerts", True):
        notifications.append(
            {
                "user_id": ctx.user["id"],
                "org_id": ctx.org["id"],
                "site_id": ctx.site["id"],
                "type": "forecast",
                "severity": "medium",
                "title": "Possibile aumento costi in arrivo",
                "message": f"Previsione 30 giorni: EUR {analysis['prediction']['next_30_days_cost_eur']:.2f} ({analysis['prediction']['expected_variation_pct']:.1f}%).",
                "read": False,
                "created_at": utc_now(),
            }
        )
    if analysis.get("advices"):
        top_advice = analysis["advices"][0]
        notifications.append(
            {
                "user_id": ctx.user["id"],
                "org_id": ctx.org["id"],
                "site_id": ctx.site["id"],
                "type": "savings",
                "severity": "low",
                "title": "Nuova opportunità di risparmio",
                "message": f"{top_advice['title']} · potenziale EUR {top_advice['monthly_savings_eur']:.2f}/mese.",
                "read": False,
                "created_at": utc_now(),
            }
        )
    if notifications:
        await db.notifications.insert_many(notifications)

    if preferences.get("email_enabled"):
        await db.notification_events.insert_one(
            {
                "user_id": ctx.user["id"],
                "org_id": ctx.org["id"],
                "site_id": ctx.site["id"],
                "mode": EMAIL_DELIVERY_MODE,
                "status": "logged",
                "event_type": "analysis_summary",
                "created_at": utc_now(),
                "payload": {
                    "advices": len(analysis.get("advices") or []),
                    "anomalies": len(analysis.get("anomalies") or []),
                    "forecast_alert": analysis.get("prediction", {}).get("alert", False),
                },
            }
        )


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf_bytes(title: str, lines: List[str]) -> bytes:
    content_rows = ["BT", "/F1 12 Tf", "1 0 0 1 48 770 Tm"]
    safe_lines = [title, *lines][:38]
    for index, line in enumerate(safe_lines):
        command = f"({_pdf_escape(line)}) Tj"
        if index == 0:
            content_rows.append(command)
        else:
            content_rows.extend(["0 -18 Td", command])
    content_rows.append("ET")
    stream = "\n".join(content_rows)
    objects = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\nendobj\n",
        f"4 0 obj\n<< /Length {len(stream.encode('latin-1', errors='ignore'))} >>\nstream\n{stream}\nendstream\nendobj\n",
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    pdf = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf.encode("latin-1", errors="ignore")))
        pdf += obj
    xref_start = len(pdf.encode("latin-1", errors="ignore"))
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n"
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF"
    return pdf.encode("latin-1", errors="ignore")


async def store_report_file(ctx: AuthContext, analysis_doc: Dict[str, Any]) -> Dict[str, Any]:
    analysis = analysis_doc["analysis"]
    lines = [
        f"Azienda: {ctx.org['name']}",
        f"Sede: {ctx.site['name']} - {ctx.site.get('city', '')}",
        f"Generato: {to_iso(utc_now())}",
        "",
        f"Costo totale osservato: EUR {analysis['kpis']['total_cost_eur']:.2f}",
        f"Consumo totale osservato: {analysis['kpis']['total_consumption_kwh']:.2f} kWh",
        f"Sprechi stimati: EUR {analysis['kpis']['estimated_waste_eur']:.2f}",
        f"Risparmio potenziale mensile: EUR {analysis['kpis']['potential_monthly_savings_eur']:.2f}",
        f"Previsione prossimi 30 giorni: EUR {analysis['prediction']['next_30_days_cost_eur']:.2f}",
        "",
        "Top consigli:",
    ]
    for advice in analysis.get("advices", [])[:3]:
        lines.append(f"- {advice['title']} | EUR {advice['monthly_savings_eur']:.2f}/mese | ROI {advice['roi_pct_year_1']:.1f}%")
    if analysis.get("anomalies"):
        lines.append("")
        lines.append("Ultime anomalie:")
        for anomaly in analysis["anomalies"][:3]:
            lines.append(f"- {anomaly['timestamp']} | EUR {anomaly['estimated_loss_eur']:.2f} | {anomaly['reasons'][0]}")

    filename = f"report-{ctx.site['id']}-{utc_now().strftime('%Y%m%d%H%M%S')}.pdf"
    file_path = REPORTS_DIR / filename
    file_path.write_bytes(build_pdf_bytes("Energy Saver Monthly Report", lines))
    report_doc = {
        "user_id": ctx.user["id"],
        "org_id": ctx.org["id"],
        "site_id": ctx.site["id"],
        "filename": filename,
        "relative_path": str(file_path.relative_to(ROOT_DIR)),
        "download_path": f"/api/reports/{filename}/download-by-name",
        "created_at": utc_now(),
        "summary": {
            "potential_monthly_savings_eur": analysis["kpis"]["potential_monthly_savings_eur"],
            "estimated_waste_eur": analysis["kpis"]["estimated_waste_eur"],
        },
    }
    result = await db.reports.insert_one(report_doc)
    report_doc["_id"] = result.inserted_id
    return report_doc


@api_router.get("/")
async def root():
    return {"message": "Energy Saver API online"}


@api_router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "energy-saver-backend",
        "timestamp": to_iso(utc_now()),
        "environment": APP_ENV,
    }


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.model_dump())
    doc = status_obj.model_dump()
    doc["timestamp"] = to_iso(doc["timestamp"])
    await db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check.get("timestamp"), str):
            check["timestamp"] = datetime.fromisoformat(check["timestamp"])
    return status_checks


@api_router.post("/auth/dev-login")
async def dev_login(payload: DevLoginRequest, response: Response):
    if APP_ENV == "production":
        raise HTTPException(status_code=403, detail="Dev login disabilitato in produzione")
    user, org, site = await bootstrap_user(payload.email, payload.name, provider="dev-bypass", company_name=payload.company_name)
    token = create_session_token(str(user["_id"]), str(org["_id"]), str(site["_id"]), payload.email)
    set_auth_cookie(response, token)
    return {
        "status": "success",
        "session": build_session_payload(user, org, site),
    }


@api_router.get("/auth/google/start")
async def google_auth_start(next_path: str = "/dashboard"):
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        raise HTTPException(status_code=503, detail="Google OAuth non configurato")
    return RedirectResponse(get_google_auth_url(next_path), status_code=302)


@api_router.get("/auth/google/callback")
async def google_auth_callback(request: Request, response: Response, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    base_frontend = FRONTEND_APP_URL or str(request.base_url).rstrip("/")
    if error:
        return RedirectResponse(f"{base_frontend}/login?auth_error={error}")
    if not code:
        return RedirectResponse(f"{base_frontend}/login?auth_error=missing_code")

    token_data = exchange_google_code(code)
    user_info = fetch_google_userinfo(token_data["access_token"])
    user, org, site = await bootstrap_user(
        user_info.get("email", ""),
        user_info.get("name", "Google User"),
        provider="google",
        google_id=user_info.get("sub"),
        company_name=user_info.get("hd") or "Energy Saver",
    )
    session_token = create_session_token(str(user["_id"]), str(org["_id"]), str(site["_id"]), user_info.get("email", ""))
    state_payload = decode_google_state(state or "")
    redirect_path = state_payload.get("next_path", "/dashboard")
    redirect_response = RedirectResponse(f"{base_frontend}/auth/callback?status=success&next={redirect_path}", status_code=302)
    set_auth_cookie(redirect_response, session_token)
    return redirect_response


@api_router.get("/auth/me")
async def auth_me(ctx: AuthContext = Depends(get_auth_context)):
    preferences = await ensure_preferences(ctx.user["id"], ctx.org["id"], ctx.site["id"])
    return {
        "authenticated": True,
        "session": build_session_payload(
            {"_id": ObjectId(ctx.user["id"]), **ctx.user},
            {"_id": ObjectId(ctx.org["id"]), **ctx.org},
            {"_id": ObjectId(ctx.site["id"]), **ctx.site},
        ),
        "notification_preferences": serialize_doc(preferences),
    }


@api_router.post("/auth/logout")
async def logout(response: Response):
    clear_auth_cookie(response)
    return {"status": "success"}


@api_router.get("/onboarding/state")
async def onboarding_state(ctx: AuthContext = Depends(get_auth_context)):
    return {
        "org": ctx.org,
        "site": ctx.site,
    }


@api_router.post("/onboarding/complete")
async def onboarding_complete(payload: OnboardingRequest, ctx: AuthContext = Depends(get_auth_context)):
    await db.orgs.update_one(
        {"_id": to_object_id(ctx.org["id"])},
        {"$set": {"name": payload.company_name, "updated_at": utc_now()}},
    )
    await db.sites.update_one(
        {"_id": to_object_id(ctx.site["id"])},
        {
            "$set": {
                "name": payload.site_name,
                "city": payload.city,
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "business_open_hour": payload.business_open_hour,
                "business_close_hour": payload.business_close_hour,
                "sector": payload.sector,
                "savings_goal_pct": payload.savings_goal_pct,
                "onboarding_completed": True,
                "updated_at": utc_now(),
            }
        },
    )
    site = await db.sites.find_one({"_id": to_object_id(ctx.site["id"])})
    org = await db.orgs.find_one({"_id": to_object_id(ctx.org["id"])})
    return {
        "status": "success",
        "session": build_session_payload(
            {"_id": ObjectId(ctx.user["id"]), **ctx.user},
            org,
            site,
        ),
    }


@api_router.get("/poc/contracts")
async def get_contract_examples():
    return build_contract_examples()


@api_router.post("/poc/ingest-manual", response_model=StoredDocumentResponse)
async def ingest_manual_data(payload: ManualIngestRequest):
    readings = payload.readings or [ManualReading(**item) for item in build_sample_readings(days=14)]
    document = {
        "site_name": payload.site_name,
        "city": payload.city,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "created_at": utc_now(),
        "readings": [
            {
                "timestamp": to_iso(reading.timestamp if isinstance(reading, ManualReading) else parse_dt(reading["timestamp"])),
                "kwh": round(float(reading.kwh if isinstance(reading, ManualReading) else reading["kwh"]), 2),
                "cost_eur": round(float(reading.cost_eur), 2) if isinstance(reading, ManualReading) and reading.cost_eur is not None else None,
            }
            for reading in readings
        ],
    }
    result = await db.poc_manual_ingests.insert_one(document)
    return {
        "id": str(result.inserted_id),
        "created_at": to_iso(document["created_at"]),
        "payload": serialize_doc(document),
    }


@api_router.post("/poc/upload-bill")
async def poc_upload_bill(file: UploadFile = File(...)):
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Caricare un file PDF")
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File troppo grande (max 10MB)")
    stored = store_bill_file(file_bytes, file.filename)
    stored_doc = {**stored, "created_at": utc_now()}
    result = await db.poc_bills.insert_one(stored_doc)
    response = serialize_doc(stored_doc)
    response["id"] = str(result.inserted_id)
    return response


@api_router.post("/poc/run-analysis")
async def run_poc_analysis(payload: AnalysisRequest):
    if payload.dataset_id:
        dataset = await db.poc_manual_ingests.find_one({"_id": to_object_id(payload.dataset_id)})
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset non trovato")
        readings_input = dataset.get("readings", [])
    elif payload.readings:
        readings_input = [
            {
                "timestamp": to_iso(reading.timestamp),
                "kwh": round(float(reading.kwh), 2),
                "cost_eur": round(float(reading.cost_eur), 2) if reading.cost_eur is not None else None,
            }
            for reading in payload.readings
        ]
    else:
        readings_input = build_sample_readings(days=14)
    weather_context = fetch_weather_context(payload.latitude, payload.longitude)
    price_signal = fetch_energy_prices(limit=96)
    analysis = analyze_dataset(
        site_name=payload.site_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        readings=readings_input,
        weather_context=weather_context,
        price_signal=price_signal,
    )
    analysis_record = {
        "site_name": payload.site_name,
        "city": payload.city,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "created_at": utc_now(),
        "weather_context": weather_context,
        "price_signal_summary": {
            "status": price_signal.get("status"),
            "source": price_signal.get("source"),
            "items_count": len(price_signal.get("items") or []),
        },
        "analysis": analysis,
    }
    result = await db.poc_analysis_runs.insert_one(analysis_record)
    return {
        "id": str(result.inserted_id),
        "created_at": to_iso(analysis_record["created_at"]),
        "weather_context": weather_context,
        "price_signal_summary": analysis_record["price_signal_summary"],
        "analysis": analysis,
    }


@api_router.get("/poc/latest-analysis")
async def latest_poc_analysis():
    latest = await db.poc_analysis_runs.find().sort("created_at", -1).limit(1).to_list(1)
    if not latest:
        raise HTTPException(status_code=404, detail="Nessuna analisi disponibile")
    return serialize_doc(latest[0])


@api_router.post("/bills/upload")
async def upload_bill(file: UploadFile = File(...), ctx: AuthContext = Depends(get_auth_context)):
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Caricare un file PDF")
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File troppo grande (max 10MB)")
    stored = store_bill_file(file_bytes, file.filename)
    bill_doc = {
        **stored,
        "user_id": ctx.user["id"],
        "org_id": ctx.org["id"],
        "site_id": ctx.site["id"],
        "notes": "",
        "uploaded_at": utc_now(),
    }
    result = await db.bills.insert_one(bill_doc)
    bill_doc["_id"] = result.inserted_id
    return {"status": "success", "bill": serialize_doc(bill_doc)}


@api_router.get("/bills")
async def list_bills(ctx: AuthContext = Depends(get_auth_context)):
    bills = await db.bills.find({"org_id": ctx.org["id"], "site_id": ctx.site["id"]}).sort("uploaded_at", -1).to_list(200)
    return {"items": [serialize_doc(item) for item in bills]}


@api_router.get("/bills/{bill_id}")
async def bill_detail(bill_id: str, ctx: AuthContext = Depends(get_auth_context)):
    bill = await db.bills.find_one({"_id": to_object_id(bill_id), "org_id": ctx.org["id"]})
    if not bill:
        raise HTTPException(status_code=404, detail="Bolletta non trovata")
    return {"bill": serialize_doc(bill)}


@api_router.patch("/bills/{bill_id}")
async def review_bill(bill_id: str, payload: BillReviewPayload, ctx: AuthContext = Depends(get_auth_context)):
    bill = await db.bills.find_one({"_id": to_object_id(bill_id), "org_id": ctx.org["id"]})
    if not bill:
        raise HTTPException(status_code=404, detail="Bolletta non trovata")
    extracted_fields = bill.get("extracted_fields", {})
    updated_fields = {**extracted_fields}
    for key in ("consumption_kwh", "total_cost_eur", "period_start", "period_end"):
        value = getattr(payload, key)
        if value is not None:
            updated_fields[key] = value
    extraction_status = "parsed" if updated_fields.get("consumption_kwh") or updated_fields.get("total_cost_eur") else "needs_manual_review"
    await db.bills.update_one(
        {"_id": bill["_id"]},
        {
            "$set": {
                "extracted_fields": updated_fields,
                "notes": payload.notes or bill.get("notes", ""),
                "extraction_status": extraction_status,
                "updated_at": utc_now(),
            }
        },
    )
    updated = await db.bills.find_one({"_id": bill["_id"]})
    return {"status": "success", "bill": serialize_doc(updated)}


@api_router.post("/consumption")
async def create_consumption_entry(payload: ConsumptionEntryCreate, ctx: AuthContext = Depends(get_auth_context)):
    doc = {
        "user_id": ctx.user["id"],
        "org_id": ctx.org["id"],
        "site_id": ctx.site["id"],
        "timestamp": payload.timestamp,
        "kwh": payload.kwh,
        "cost_eur": payload.cost_eur,
        "note": payload.note,
        "created_at": utc_now(),
    }
    result = await db.consumption_readings.insert_one(doc)
    doc["_id"] = result.inserted_id
    return {"status": "success", "entry": serialize_doc(doc)}


@api_router.post("/consumption/batch")
async def create_consumption_batch(payload: ConsumptionBatchRequest, ctx: AuthContext = Depends(get_auth_context)):
    docs = [
        {
            "user_id": ctx.user["id"],
            "org_id": ctx.org["id"],
            "site_id": ctx.site["id"],
            "timestamp": entry.timestamp,
            "kwh": entry.kwh,
            "cost_eur": entry.cost_eur,
            "note": entry.note,
            "created_at": utc_now(),
        }
        for entry in payload.entries
    ]
    if not docs:
        raise HTTPException(status_code=400, detail="Nessuna riga da importare")
    result = await db.consumption_readings.insert_many(docs)
    for index, inserted_id in enumerate(result.inserted_ids):
        docs[index]["_id"] = inserted_id
    return {"status": "success", "count": len(docs), "items": [serialize_doc(doc) for doc in docs]}


@api_router.get("/consumption")
async def list_consumption(ctx: AuthContext = Depends(get_auth_context)):
    items = await db.consumption_readings.find({"org_id": ctx.org["id"], "site_id": ctx.site["id"]}).sort("timestamp", -1).to_list(500)
    return {"items": [serialize_doc(item) for item in items]}


@api_router.delete("/consumption/{entry_id}")
async def delete_consumption_entry(entry_id: str, ctx: AuthContext = Depends(get_auth_context)):
    result = await db.consumption_readings.delete_one({"_id": to_object_id(entry_id), "org_id": ctx.org["id"]})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Voce non trovata")
    return {"status": "success"}


@api_router.post("/analytics/run")
async def run_analysis(ctx: AuthContext = Depends(get_auth_context)):
    readings = await gather_site_readings(ctx.site["id"])
    if not readings:
        raise HTTPException(status_code=400, detail="Aggiungi almeno una bolletta o un consumo manuale prima di lanciare l’analisi")
    weather_context = fetch_weather_context(float(ctx.site.get("latitude") or DEFAULT_LATITUDE), float(ctx.site.get("longitude") or DEFAULT_LONGITUDE))
    price_signal = fetch_energy_prices(limit=96)
    analysis = analyze_dataset(
        site_name=ctx.site.get("name") or "Sede principale",
        latitude=float(ctx.site.get("latitude") or DEFAULT_LATITUDE),
        longitude=float(ctx.site.get("longitude") or DEFAULT_LONGITUDE),
        readings=readings,
        weather_context=weather_context,
        price_signal=price_signal,
    )
    analysis_doc = {
        "user_id": ctx.user["id"],
        "org_id": ctx.org["id"],
        "site_id": ctx.site["id"],
        "created_at": utc_now(),
        "weather_context": weather_context,
        "price_signal_summary": {
            "status": price_signal.get("status"),
            "source": price_signal.get("source"),
            "items_count": len(price_signal.get("items") or []),
        },
        "analysis": analysis,
    }
    result = await db.analytics_runs.insert_one(analysis_doc)
    analysis_doc["_id"] = result.inserted_id
    await create_notifications_from_analysis(ctx, analysis_doc)
    return {"status": "success", "analysis_run": serialize_doc(analysis_doc)}


@api_router.get("/analytics/latest")
async def get_latest_analysis(ctx: AuthContext = Depends(get_auth_context)):
    latest = await latest_analysis_for_site(ctx.site["id"])
    return {"analysis_run": serialize_doc(latest) if latest else None}


@api_router.get("/notifications")
async def list_notifications(ctx: AuthContext = Depends(get_auth_context)):
    items = await db.notifications.find({"user_id": ctx.user["id"], "site_id": ctx.site["id"]}).sort("created_at", -1).to_list(200)
    unread = sum(1 for item in items if not item.get("read"))
    return {"items": [serialize_doc(item) for item in items], "unread_count": unread}


@api_router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(ctx: AuthContext = Depends(get_auth_context)):
    await db.notifications.update_many({"user_id": ctx.user["id"], "site_id": ctx.site["id"], "read": False}, {"$set": {"read": True, "updated_at": utc_now()}})
    return {"status": "success"}


@api_router.get("/notifications/preferences")
async def get_notification_preferences(ctx: AuthContext = Depends(get_auth_context)):
    preferences = await ensure_preferences(ctx.user["id"], ctx.org["id"], ctx.site["id"])
    return {"preferences": serialize_doc(preferences)}


@api_router.post("/notifications/preferences")
async def update_notification_preferences(payload: NotificationPreferencesPayload, ctx: AuthContext = Depends(get_auth_context)):
    await db.notification_preferences.update_one(
        {"user_id": ctx.user["id"], "site_id": ctx.site["id"]},
        {
            "$set": {
                "email_enabled": payload.email_enabled,
                "anomaly_alerts": payload.anomaly_alerts,
                "price_alerts": payload.price_alerts,
                "report_alerts": payload.report_alerts,
                "updated_at": utc_now(),
            },
            "$setOnInsert": {
                "org_id": ctx.org["id"],
                "created_at": utc_now(),
            },
        },
        upsert=True,
    )
    preferences = await ensure_preferences(ctx.user["id"], ctx.org["id"], ctx.site["id"])
    return {"status": "success", "preferences": serialize_doc(preferences)}


@api_router.post("/notifications/test-email")
async def send_test_email(ctx: AuthContext = Depends(get_auth_context)):
    preferences = await ensure_preferences(ctx.user["id"], ctx.org["id"], ctx.site["id"])
    event = {
        "user_id": ctx.user["id"],
        "org_id": ctx.org["id"],
        "site_id": ctx.site["id"],
        "mode": EMAIL_DELIVERY_MODE,
        "status": "logged",
        "event_type": "manual_test",
        "created_at": utc_now(),
        "payload": {
            "email": ctx.user["email"],
            "email_enabled": preferences.get("email_enabled", False),
        },
    }
    result = await db.notification_events.insert_one(event)
    event["_id"] = result.inserted_id
    return {
        "status": "success",
        "message": "Invio registrato in modalità sviluppo interna",
        "event": serialize_doc(event),
    }


@api_router.get("/dashboard/overview")
async def dashboard_overview(ctx: AuthContext = Depends(get_auth_context)):
    bills = await db.bills.find({"org_id": ctx.org["id"], "site_id": ctx.site["id"]}).sort("uploaded_at", -1).to_list(5)
    readings_count = await db.consumption_readings.count_documents({"org_id": ctx.org["id"], "site_id": ctx.site["id"]})
    reports_count = await db.reports.count_documents({"org_id": ctx.org["id"], "site_id": ctx.site["id"]})
    notifications = await db.notifications.find({"user_id": ctx.user["id"], "site_id": ctx.site["id"]}).sort("created_at", -1).to_list(6)
    unread_notifications = sum(1 for item in notifications if not item.get("read"))
    latest = await latest_analysis_for_site(ctx.site["id"])
    weather_status = fetch_weather_context(float(ctx.site.get("latitude") or DEFAULT_LATITUDE), float(ctx.site.get("longitude") or DEFAULT_LONGITUDE)).get("status")
    price_status = fetch_energy_prices(limit=24).get("status")
    return {
        "session": build_session_payload(
            {"_id": ObjectId(ctx.user["id"]), **ctx.user},
            {"_id": ObjectId(ctx.org["id"]), **ctx.org},
            {"_id": ObjectId(ctx.site["id"]), **ctx.site},
        ),
        "integration_status": {
            "weather": weather_status,
            "prices": price_status,
            "email_mode": EMAIL_DELIVERY_MODE,
            "google_oauth_configured": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")),
        },
        "counts": {
            "bills": len(bills),
            "readings": readings_count,
            "reports": reports_count,
            "unread_notifications": unread_notifications,
        },
        "latest_analysis": serialize_doc(latest),
        "recent_bills": [serialize_doc(item) for item in bills],
        "notifications": [serialize_doc(item) for item in notifications],
    }


@api_router.get("/settings/summary")
async def settings_summary(ctx: AuthContext = Depends(get_auth_context)):
    preferences = await ensure_preferences(ctx.user["id"], ctx.org["id"], ctx.site["id"])
    return {
        "org": ctx.org,
        "site": ctx.site,
        "preferences": serialize_doc(preferences),
        "integrations": {
            "weather_provider": "OpenWeather",
            "price_provider": "energy-charts",
            "google_oauth": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")),
            "email_mode": EMAIL_DELIVERY_MODE,
            "file_storage": os.getenv("FILE_STORAGE_MODE", "local_secure"),
        },
    }


@api_router.post("/reports/generate")
async def generate_report(ctx: AuthContext = Depends(get_auth_context)):
    latest = await latest_analysis_for_site(ctx.site["id"])
    if not latest:
        raise HTTPException(status_code=400, detail="Esegui prima un’analisi per generare il report")
    report_doc = await store_report_file(ctx, latest)
    return {
        "status": "success",
        "report": serialize_doc(report_doc),
    }


@api_router.get("/reports")
async def list_reports(ctx: AuthContext = Depends(get_auth_context)):
    items = await db.reports.find({"org_id": ctx.org["id"], "site_id": ctx.site["id"]}).sort("created_at", -1).to_list(100)
    reports = []
    for item in items:
        serialized = serialize_doc(item)
        serialized["download_url"] = f"/api/reports/{serialized['id']}/download"
        reports.append(serialized)
    return {"items": reports}


@api_router.get("/reports/{report_id}/download")
async def download_report(report_id: str, ctx: AuthContext = Depends(get_auth_context)):
    report = await db.reports.find_one({"_id": to_object_id(report_id), "org_id": ctx.org["id"]})
    if not report:
        raise HTTPException(status_code=404, detail="Report non trovato")
    file_path = ROOT_DIR / report["relative_path"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File report non disponibile")
    return FileResponse(path=file_path, filename=report["filename"], media_type="application/pdf")


@api_router.get("/reports/{filename}/download-by-name")
async def download_report_by_name(filename: str, ctx: AuthContext = Depends(get_auth_context)):
    file_path = REPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report non trovato")
    return FileResponse(path=file_path, filename=filename, media_type="application/pdf")


app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
