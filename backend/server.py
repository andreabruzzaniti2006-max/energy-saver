from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging
import os
import uuid

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
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Energy Saver SaaS API", version="0.1.0")
api_router = APIRouter(prefix="/api")


class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


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


def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    serialized: Dict[str, Any] = {}
    for key, value in doc.items():
        if key == "_id":
            serialized["id"] = str(value)
        elif isinstance(value, datetime):
            serialized[key] = to_iso(value)
        elif isinstance(value, list):
            serialized[key] = [serialize_doc(item) if isinstance(item, dict) else (to_iso(item) if isinstance(item, datetime) else item) for item in value]
        elif isinstance(value, dict):
            serialized[key] = serialize_doc(value)
        else:
            serialized[key] = value
    return serialized


@api_router.get("/")
async def root():
    return {"message": "Energy Saver API online"}


@api_router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "energy-saver-backend",
        "timestamp": to_iso(datetime.now(timezone.utc)),
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
        "created_at": datetime.now(timezone.utc),
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
async def upload_bill(file: UploadFile = File(...)):
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Caricare un file PDF")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File troppo grande (max 10MB)")

    stored = store_bill_file(file_bytes, file.filename)
    stored_doc = {**stored, "created_at": datetime.now(timezone.utc)}
    result = await db.poc_bills.insert_one(stored_doc)
    response = serialize_doc(stored_doc)
    response["id"] = str(result.inserted_id)
    return response


@api_router.post("/poc/run-analysis")
async def run_poc_analysis(payload: AnalysisRequest):
    readings_input: List[Dict[str, Any]]

    if payload.dataset_id:
        dataset = await db.poc_manual_ingests.find_one({"_id": payload.dataset_id})
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
        "created_at": datetime.now(timezone.utc),
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
async def latest_analysis():
    latest = await db.poc_analysis_runs.find().sort("created_at", -1).limit(1).to_list(1)
    if not latest:
        raise HTTPException(status_code=404, detail="Nessuna analisi disponibile")
    return serialize_doc(latest[0])


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
