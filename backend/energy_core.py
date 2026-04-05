import hashlib
import json
import logging
import os
import re
import statistics
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import requests

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
CACHE_DIR = ROOT_DIR / "cache"
UPLOADS_DIR = ROOT_DIR / "uploads"
CACHE_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

DEFAULT_LATITUDE = 45.4642
DEFAULT_LONGITUDE = 9.19
DEFAULT_CITY = "Milano"
BUSINESS_OPEN_HOUR = 6
BUSINESS_CLOSE_HOUR = 18


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def load_json_cache(key: str, ttl_seconds: int) -> Optional[Dict[str, Any]]:
    cache_path = CACHE_DIR / f"{key}.json"
    if not cache_path.exists():
        return None
    age = utc_now().timestamp() - cache_path.stat().st_mtime
    if age > ttl_seconds:
        return None
    try:
        return json.loads(cache_path.read_text())
    except Exception:
        return None


def save_json_cache(key: str, data: Dict[str, Any]) -> None:
    cache_path = CACHE_DIR / f"{key}.json"
    cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def hash_key(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def fetch_weather_context(latitude: float, longitude: float) -> Dict[str, Any]:
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        return {
            "status": "error",
            "source": "openweather",
            "error": "OPENWEATHER_API_KEY mancante",
        }

    cache_key = hash_key(f"weather:{round(latitude, 3)}:{round(longitude, 3)}")
    cached = load_json_cache(cache_key, ttl_seconds=1800)
    if cached:
        cached["cached"] = True
        return cached

    url = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5/weather")
    try:
        response = requests.get(
            url,
            params={
                "lat": latitude,
                "lon": longitude,
                "appid": api_key,
                "units": "metric",
                "lang": "it",
            },
            timeout=20,
        )
        if response.status_code != 200:
            return {
                "status": "error",
                "source": "openweather",
                "error": response.text[:300],
                "http_status": response.status_code,
            }
        payload = response.json()
        result = {
            "status": "ok",
            "source": "openweather",
            "cached": False,
            "city": payload.get("name"),
            "temperature_c": payload.get("main", {}).get("temp"),
            "humidity_pct": payload.get("main", {}).get("humidity"),
            "wind_speed_ms": payload.get("wind", {}).get("speed"),
            "weather": (payload.get("weather") or [{}])[0].get("description"),
            "retrieved_at": to_iso(utc_now()),
        }
        save_json_cache(cache_key, result)
        return result
    except Exception as exc:
        logger.exception("Errore durante il recupero meteo")
        return {
            "status": "error",
            "source": "openweather",
            "error": str(exc),
        }


def _fallback_price_series(limit: int = 96) -> Dict[str, Any]:
    now = utc_now().replace(minute=0, second=0, microsecond=0)
    items: List[Dict[str, Any]] = []
    for offset in range(limit):
        moment = now - timedelta(hours=limit - offset)
        hour = moment.hour
        base = 0.21
        if 7 <= hour <= 10:
            base *= 1.18
        elif 18 <= hour <= 21:
            base *= 1.25
        elif 0 <= hour <= 5:
            base *= 0.82
        items.append(
            {
                "timestamp": to_iso(moment),
                "hour": hour,
                "price_eur_per_mwh": round(base * 1000, 2),
                "price_eur_per_kwh": round(base, 4),
            }
        )
    return {
        "status": "fallback",
        "source": "historical_profile",
        "items": items,
        "unit": "EUR/kWh",
        "retrieved_at": to_iso(utc_now()),
    }


def fetch_energy_prices(limit: int = 96) -> Dict[str, Any]:
    cache_key = hash_key(f"prices:{limit}")
    cached = load_json_cache(cache_key, ttl_seconds=1800)
    if cached:
        cached["cached"] = True
        return cached

    url = os.getenv("ENERGY_PRICE_API_URL", "https://api.energy-charts.info/price?bzn=IT-North")
    try:
        response = requests.get(url, timeout=25)
        if response.status_code != 200:
            logger.warning("Price API error %s", response.status_code)
            fallback = _fallback_price_series(limit=limit)
            save_json_cache(cache_key, fallback)
            return fallback

        payload = response.json()
        unix_seconds = payload.get("unix_seconds") or []
        prices = payload.get("price") or []
        items: List[Dict[str, Any]] = []
        for timestamp, price_eur_mwh in list(zip(unix_seconds, prices))[-limit:]:
            moment = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            items.append(
                {
                    "timestamp": to_iso(moment),
                    "hour": moment.hour,
                    "price_eur_per_mwh": round(float(price_eur_mwh), 2),
                    "price_eur_per_kwh": round(float(price_eur_mwh) / 1000.0, 4),
                }
            )
        result = {
            "status": "ok",
            "source": "energy-charts",
            "cached": False,
            "unit": "EUR/kWh",
            "items": items,
            "retrieved_at": to_iso(utc_now()),
        }
        save_json_cache(cache_key, result)
        return result
    except Exception as exc:
        logger.exception("Errore durante il recupero prezzi")
        fallback = _fallback_price_series(limit=limit)
        fallback["error"] = str(exc)
        save_json_cache(cache_key, fallback)
        return fallback


def build_price_profile(price_signal: Dict[str, Any]) -> Dict[int, float]:
    items = price_signal.get("items") or []
    grouped: Dict[int, List[float]] = {hour: [] for hour in range(24)}
    for item in items:
        grouped[item["hour"]].append(float(item["price_eur_per_kwh"]))
    profile: Dict[int, float] = {}
    all_prices = [float(item["price_eur_per_kwh"]) for item in items] or [0.24]
    default_price = round(float(statistics.mean(all_prices)), 4)
    for hour in range(24):
        profile[hour] = round(float(statistics.mean(grouped[hour])), 4) if grouped[hour] else default_price
    return profile


def build_sample_readings(days: int = 14) -> List[Dict[str, Any]]:
    start = utc_now().replace(minute=0, second=0, microsecond=0) - timedelta(days=days)
    readings: List[Dict[str, Any]] = []
    for idx in range(days * 24):
        moment = start + timedelta(hours=idx)
        weekday = moment.weekday()
        business_hours = BUSINESS_OPEN_HOUR <= moment.hour <= BUSINESS_CLOSE_HOUR
        is_weekend = weekday >= 5
        base = 6.2
        if business_hours:
            base = 14.8 if not is_weekend else 9.4
        if 12 <= moment.hour <= 14:
            base += 2.4
        if 7 <= moment.hour <= 9:
            base += 1.3
        if moment.hour in (21, 22) and moment.day % 4 == 0:
            base += 8.5
        if moment.hour in (2, 3) and moment.day % 5 == 0:
            base += 4.1
        readings.append(
            {
                "timestamp": to_iso(moment),
                "kwh": round(base, 2),
                "source": "sample_generated",
            }
        )
    return readings


def enrich_readings_with_cost(readings: List[Dict[str, Any]], price_signal: Dict[str, Any]) -> List[Dict[str, Any]]:
    price_profile = build_price_profile(price_signal)
    enriched: List[Dict[str, Any]] = []
    for reading in readings:
        moment = parse_dt(reading["timestamp"])
        price = float(reading.get("price_eur_per_kwh") or price_profile[moment.hour])
        kwh = float(reading["kwh"])
        enriched.append(
            {
                **reading,
                "timestamp": to_iso(moment),
                "price_eur_per_kwh": round(price, 4),
                "cost_eur": round(float(reading.get("cost_eur") or (kwh * price)), 2),
                "hour": moment.hour,
                "weekday": moment.weekday(),
            }
        )
    return enriched


def detect_anomalies(enriched_readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    values = [item["kwh"] for item in enriched_readings]
    mean_kwh = float(statistics.mean(values)) if values else 0.0
    std_kwh = float(statistics.pstdev(values)) if len(values) > 1 else 0.0
    threshold = mean_kwh + max(1.6 * std_kwh, 3.5)
    anomalies: List[Dict[str, Any]] = []
    for item in enriched_readings:
        reasons: List[str] = []
        excess_kwh = max(0.0, float(item["kwh"]) - mean_kwh)
        if float(item["kwh"]) >= threshold:
            reasons.append("consumo superiore alla baseline statistica")
        if (item["hour"] < BUSINESS_OPEN_HOUR or item["hour"] > BUSINESS_CLOSE_HOUR) and float(item["kwh"]) > max(8.0, mean_kwh):
            reasons.append("carico elevato fuori orario")
        if item["weekday"] >= 5 and float(item["kwh"]) > mean_kwh * 1.18:
            reasons.append("utilizzo anomalo nel weekend")
        if reasons:
            anomalies.append(
                {
                    "timestamp": item["timestamp"],
                    "kwh": item["kwh"],
                    "cost_eur": item["cost_eur"],
                    "excess_kwh": round(excess_kwh, 2),
                    "estimated_loss_eur": round(excess_kwh * float(item["price_eur_per_kwh"]), 2),
                    "reasons": reasons,
                }
            )
    return anomalies


def _daily_series(enriched_readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    daily: Dict[str, Dict[str, Any]] = {}
    for item in enriched_readings:
        day_key = parse_dt(item["timestamp"]).date().isoformat()
        if day_key not in daily:
            daily[day_key] = {"date": day_key, "kwh": 0.0, "cost_eur": 0.0}
        daily[day_key]["kwh"] += float(item["kwh"])
        daily[day_key]["cost_eur"] += float(item["cost_eur"])
    ordered = [
        {
            "date": key,
            "kwh": round(value["kwh"], 2),
            "cost_eur": round(value["cost_eur"], 2),
        }
        for key, value in sorted(daily.items())
    ]
    return ordered


def build_advices(
    enriched_readings: List[Dict[str, Any]],
    anomalies: List[Dict[str, Any]],
    weather_context: Dict[str, Any],
    price_signal: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if not enriched_readings:
        return []

    avg_price = statistics.mean([item["price_eur_per_kwh"] for item in enriched_readings])
    night_load = [item["kwh"] for item in enriched_readings if item["hour"] < 6 or item["hour"] > 21]
    day_load = [item["kwh"] for item in enriched_readings if 8 <= item["hour"] <= 18]
    after_hours = [an for an in anomalies if any("fuori orario" in reason for reason in an["reasons"])]
    weekend = [an for an in anomalies if any("weekend" in reason for reason in an["reasons"])]
    peak_prices = [item["price_eur_per_kwh"] for item in (price_signal.get("items") or []) if item["hour"] in range(18, 22)]
    offpeak_prices = [item["price_eur_per_kwh"] for item in (price_signal.get("items") or []) if item["hour"] in range(0, 6)]

    advices: List[Dict[str, Any]] = []

    if after_hours:
        excess = sum(item["excess_kwh"] for item in after_hours) / max(1, len({parse_dt(item['timestamp']).date() for item in after_hours}))
        monthly_saving = round(excess * avg_price * 30, 2)
        advices.append(
            {
                "title": "Spegni i carichi residui dopo le 18:30",
                "priority": "high",
                "monthly_savings_eur": monthly_saving,
                "estimated_investment_eur": 120.0,
                "payback_months": round(120.0 / max(monthly_saving, 1), 1),
                "roi_pct_year_1": round(((monthly_saving * 12) - 120.0) / 120.0 * 100, 1),
                "reason": f"Rilevati {len(after_hours)} picchi fuori orario con spreco medio di {round(excess, 1)} kWh/giorno.",
                "action": "Imposta checklist di chiusura o smart plug per attrezzature non critiche.",
            }
        )

    if night_load and day_load and statistics.mean(night_load) > statistics.mean(day_load) * 0.45:
        monthly_saving = round(statistics.mean(night_load) * avg_price * 20, 2)
        advices.append(
            {
                "title": "Riduci il baseload notturno",
                "priority": "high",
                "monthly_savings_eur": monthly_saving,
                "estimated_investment_eur": 180.0,
                "payback_months": round(180.0 / max(monthly_saving, 1), 1),
                "roi_pct_year_1": round(((monthly_saving * 12) - 180.0) / 180.0 * 100, 1),
                "reason": "Il consumo notturno resta troppo alto rispetto all’orario operativo.",
                "action": "Verifica frigoriferi, standby, insegne e ventilazione continua.",
            }
        )

    if peak_prices and offpeak_prices and statistics.mean(peak_prices) > statistics.mean(offpeak_prices) * 1.18:
        shiftable_load = statistics.mean(day_load[-20:] if len(day_load) >= 20 else day_load) * 0.18 if day_load else 3.5
        monthly_saving = round(shiftable_load * (statistics.mean(peak_prices) - statistics.mean(offpeak_prices)) * 22, 2)
        advices.append(
            {
                "title": "Sposta i carichi flessibili fuori fascia di picco",
                "priority": "medium",
                "monthly_savings_eur": monthly_saving,
                "estimated_investment_eur": 60.0,
                "payback_months": round(60.0 / max(monthly_saving, 1), 1),
                "roi_pct_year_1": round(((monthly_saving * 12) - 60.0) / 60.0 * 100, 1),
                "reason": "Il differenziale tra prezzo serale e notturno è sufficiente per ottimizzare carichi differibili.",
                "action": "Programma lavastoviglie, ricariche e pre-raffrescamento prima delle 18:00 o dopo le 22:00.",
            }
        )

    current_temp = weather_context.get("temperature_c") if weather_context.get("status") == "ok" else None
    if current_temp is not None and (current_temp <= 8 or current_temp >= 28):
        monthly_saving = round((statistics.mean(day_load) if day_load else 10.0) * avg_price * 12 * 0.08, 2)
        advices.append(
            {
                "title": "Ottimizza HVAC e setpoint climatici",
                "priority": "medium",
                "monthly_savings_eur": monthly_saving,
                "estimated_investment_eur": 150.0,
                "payback_months": round(150.0 / max(monthly_saving, 1), 1),
                "roi_pct_year_1": round(((monthly_saving * 12) - 150.0) / 150.0 * 100, 1),
                "reason": f"La temperatura esterna attuale ({current_temp}°C) aumenta la sensibilità del sito ai setpoint HVAC.",
                "action": "Alza o abbassa il setpoint di 1°C e usa avviamento graduale degli impianti.",
            }
        )

    if weekend:
        monthly_saving = round(sum(item["estimated_loss_eur"] for item in weekend) * 2.1, 2)
        advices.append(
            {
                "title": "Riduci i consumi nel weekend",
                "priority": "medium",
                "monthly_savings_eur": monthly_saving,
                "estimated_investment_eur": 90.0,
                "payback_months": round(90.0 / max(monthly_saving, 1), 1),
                "roi_pct_year_1": round(((monthly_saving * 12) - 90.0) / 90.0 * 100, 1),
                "reason": f"Sono emersi {len(weekend)} episodi di consumo anomalo fuori giorni tipici di attività.",
                "action": "Definisci profili di funzionamento weekend e verifica avvii automatici indesiderati.",
            }
        )

    deduped = sorted(advices, key=lambda item: item["monthly_savings_eur"], reverse=True)
    return deduped[:5]


def build_prediction(
    enriched_readings: List[Dict[str, Any]],
    weather_context: Dict[str, Any],
    price_signal: Dict[str, Any],
) -> Dict[str, Any]:
    daily = _daily_series(enriched_readings)
    if not daily:
        return {
            "next_30_days_cost_eur": 0.0,
            "expected_variation_pct": 0.0,
            "alert": False,
            "drivers": [],
        }

    y = np.array([item["cost_eur"] for item in daily], dtype=float)
    x = np.arange(len(y), dtype=float)
    if len(y) >= 2:
        slope, intercept = np.polyfit(x, y, 1)
        projected_daily_cost = max(float(intercept + slope * (len(y) + 1)), float(np.mean(y[-7:] if len(y) >= 7 else y)))
    else:
        projected_daily_cost = float(y[0])

    latest_prices = [item["price_eur_per_kwh"] for item in (price_signal.get("items") or [])[-24:]] or [0.24]
    historical_prices = [item["price_eur_per_kwh"] for item in (price_signal.get("items") or [])] or latest_prices
    price_multiplier = float(statistics.mean(latest_prices)) / max(float(statistics.mean(historical_prices)), 0.01)

    weather_multiplier = 1.0
    drivers: List[str] = []
    current_temp = weather_context.get("temperature_c") if weather_context.get("status") == "ok" else None
    if current_temp is not None:
        comfort_delta = max(0.0, abs(float(current_temp) - 21.0) - 3.0)
        if comfort_delta > 0:
            weather_multiplier += comfort_delta * 0.025
            drivers.append(f"temperatura esterna fuori comfort ({current_temp}°C)")

    if price_multiplier > 1.05:
        drivers.append("prezzo energia recente in aumento")
    if price_multiplier < 0.95:
        drivers.append("prezzo energia recente in calo")

    next_30_cost = round(projected_daily_cost * 30 * price_multiplier * weather_multiplier, 2)
    baseline_30_cost = round(float(np.mean(y)) * 30, 2)
    variation = round(((next_30_cost - baseline_30_cost) / max(baseline_30_cost, 1)) * 100, 2)

    return {
        "next_30_days_cost_eur": next_30_cost,
        "baseline_30_days_cost_eur": baseline_30_cost,
        "expected_variation_pct": variation,
        "alert": variation >= 10,
        "drivers": drivers or ["trend consumi storici", "profilo prezzo energia"],
    }


def analyze_dataset(
    site_name: str,
    latitude: float,
    longitude: float,
    readings: List[Dict[str, Any]],
    weather_context: Dict[str, Any],
    price_signal: Dict[str, Any],
) -> Dict[str, Any]:
    enriched = enrich_readings_with_cost(readings, price_signal)
    anomalies = detect_anomalies(enriched)
    advices = build_advices(enriched, anomalies, weather_context, price_signal)
    prediction = build_prediction(enriched, weather_context, price_signal)
    daily = _daily_series(enriched)

    total_kwh = round(sum(item["kwh"] for item in enriched), 2)
    total_cost = round(sum(item["cost_eur"] for item in enriched), 2)
    wasted_eur = round(sum(item["estimated_loss_eur"] for item in anomalies), 2)
    potential_savings = round(sum(item["monthly_savings_eur"] for item in advices), 2)

    return {
        "site_name": site_name,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "generated_at": to_iso(utc_now()),
        "kpis": {
            "total_consumption_kwh": total_kwh,
            "total_cost_eur": total_cost,
            "avg_daily_consumption_kwh": round(total_kwh / max(len(daily), 1), 2),
            "estimated_waste_eur": wasted_eur,
            "potential_monthly_savings_eur": potential_savings,
        },
        "anomalies": anomalies,
        "advices": advices,
        "prediction": prediction,
        "daily_series": daily,
        "signal_status": {
            "weather": weather_context.get("status"),
            "prices": price_signal.get("status"),
        },
    }


def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", filename or "bill.pdf")
    return cleaned[:120] or "bill.pdf"


def extract_bill_fields_from_bytes(file_bytes: bytes) -> Dict[str, Any]:
    text = file_bytes.decode("latin-1", errors="ignore")
    consumption_match = re.search(r"(\d+(?:[.,]\d+)?)\s*kwh", text, re.IGNORECASE)
    total_match = re.search(r"(?:totale|total|importo|amount|eur|€)\D{0,12}(\d+(?:[.,]\d+)?)", text, re.IGNORECASE)
    period_match = re.findall(r"(\d{2}/\d{2}/\d{4})", text)

    extracted = {
        "consumption_kwh": float(consumption_match.group(1).replace(",", ".")) if consumption_match else None,
        "total_cost_eur": float(total_match.group(1).replace(",", ".")) if total_match else None,
        "period_start": period_match[0] if len(period_match) >= 1 else None,
        "period_end": period_match[1] if len(period_match) >= 2 else None,
        "raw_text_preview": text[:280],
    }
    return extracted


def store_bill_file(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    safe_name = sanitize_filename(filename)
    file_id = str(uuid.uuid4())
    relative_path = f"uploads/{file_id}-{safe_name}"
    absolute_path = ROOT_DIR / relative_path
    absolute_path.write_bytes(file_bytes)

    has_pdf_header = file_bytes[:8].startswith(b"%PDF")
    extracted_fields = extract_bill_fields_from_bytes(file_bytes) if has_pdf_header else {
        "consumption_kwh": None,
        "total_cost_eur": None,
        "period_start": None,
        "period_end": None,
        "raw_text_preview": "",
    }
    extraction_status = "parsed" if extracted_fields.get("consumption_kwh") is not None and extracted_fields.get("total_cost_eur") is not None else ("needs_manual_review" if has_pdf_header else "invalid_pdf")

    return {
        "id": file_id,
        "filename": safe_name,
        "storage_mode": "local_secure",
        "relative_path": relative_path,
        "size_bytes": len(file_bytes),
        "uploaded_at": to_iso(utc_now()),
        "extraction_status": extraction_status,
        "extracted_fields": extracted_fields,
        "pdf_header_detected": has_pdf_header,
    }


def build_sample_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        b"BT /F1 12 Tf 72 720 Td (Consumo 1240 kWh Totale EUR 348.90 Periodo 01/03/2026 31/03/2026) Tj ET\n"
        b"%%EOF"
    )


def build_contract_examples() -> Dict[str, Any]:
    return {
        "manual_ingest": {
            "site_name": "Bar Centrale",
            "city": "Milano",
            "latitude": 45.4642,
            "longitude": 9.19,
            "readings": build_sample_readings(days=2)[:6],
        },
        "analysis_output": {
            "kpis": {
                "total_consumption_kwh": 1240.0,
                "total_cost_eur": 348.9,
                "avg_daily_consumption_kwh": 82.4,
                "estimated_waste_eur": 41.2,
                "potential_monthly_savings_eur": 126.0,
            },
            "advices": [
                {
                    "title": "Spegni i carichi residui dopo le 18:30",
                    "monthly_savings_eur": 120.0,
                    "roi_pct_year_1": 380.0,
                }
            ],
            "prediction": {
                "next_30_days_cost_eur": 392.4,
                "expected_variation_pct": 12.1,
                "alert": True,
            },
        },
    }
