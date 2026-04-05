#!/usr/bin/env python3

import requests
import sys

def debug_analytics_issue():
    base_url = "https://energy-saver-16.preview.emergentagent.com"
    session = requests.Session()
    
    # Login first
    payload = {
        "email": "demo@energysaver.app",
        "name": "Energy Saver Demo",
        "company_name": "Energy Saver Demo"
    }
    login_response = session.post(f"{base_url}/api/auth/dev-login", json=payload)
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    print("✅ Login successful")
    
    # Check what consumption data exists
    consumption_response = session.get(f"{base_url}/api/consumption")
    if consumption_response.status_code == 200:
        consumption_data = consumption_response.json()
        print(f"📊 Manual consumption entries: {len(consumption_data.get('items', []))}")
        for item in consumption_data.get('items', [])[:3]:
            print(f"  - {item.get('timestamp')}: {item.get('kwh')} kWh")
    
    # Check bills
    bills_response = session.get(f"{base_url}/api/bills")
    if bills_response.status_code == 200:
        bills_data = bills_response.json()
        print(f"📋 Bills: {len(bills_data.get('items', []))}")
        for bill in bills_data.get('items', [])[:3]:
            print(f"  - {bill.get('filename')}: {bill.get('extraction_status')}")
    
    # Try analytics
    analytics_response = session.post(f"{base_url}/api/analytics/run")
    print(f"🔬 Analytics response: {analytics_response.status_code}")
    if analytics_response.status_code == 400:
        error_data = analytics_response.json()
        print(f"   Error: {error_data.get('detail')}")
    elif analytics_response.status_code == 200:
        print("   Analytics ran successfully (this might be the issue)")

if __name__ == "__main__":
    debug_analytics_issue()