import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

load_dotenv(BACKEND_DIR / ".env")

from energy_core import (  # noqa: E402
    DEFAULT_CITY,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    analyze_dataset,
    build_contract_examples,
    build_sample_pdf_bytes,
    build_sample_readings,
    fetch_energy_prices,
    fetch_weather_context,
    store_bill_file,
)


def main() -> int:
    readings = build_sample_readings(days=14)
    weather = fetch_weather_context(DEFAULT_LATITUDE, DEFAULT_LONGITUDE)
    prices = fetch_energy_prices(limit=96)
    bill = store_bill_file(build_sample_pdf_bytes(), "sample_energy_bill.pdf")
    analysis = analyze_dataset(
        site_name="Bar Demo Milano",
        latitude=DEFAULT_LATITUDE,
        longitude=DEFAULT_LONGITUDE,
        readings=readings,
        weather_context=weather,
        price_signal=prices,
    )

    report = {
        "contracts": build_contract_examples(),
        "integrations": {
            "weather": weather,
            "prices": {
                "status": prices.get("status"),
                "source": prices.get("source"),
                "items_count": len(prices.get("items") or []),
            },
        },
        "bill_pipeline": {
            "filename": bill.get("filename"),
            "extraction_status": bill.get("extraction_status"),
            "pdf_header_detected": bill.get("pdf_header_detected"),
            "extracted_fields": bill.get("extracted_fields"),
        },
        "analysis": analysis,
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))

    failures = []
    if prices.get("status") not in {"ok", "fallback"}:
        failures.append("price_signal_unavailable")
    if bill.get("extraction_status") not in {"parsed", "needs_manual_review"}:
        failures.append("bill_upload_pipeline_failed")
    if len(analysis.get("advices") or []) < 3:
        failures.append("insufficient_advices_generated")
    if len(analysis.get("anomalies") or []) < 1:
        failures.append("anomaly_detection_failed")
    if analysis.get("prediction", {}).get("next_30_days_cost_eur", 0) <= 0:
        failures.append("prediction_failed")
    if weather.get("status") != "ok":
        failures.append("openweather_call_failed")

    if failures:
        print("\nPOC FAILURES:", ", ".join(failures), file=sys.stderr)
        return 1

    print("\nPOC SUCCESS: core workflow validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
