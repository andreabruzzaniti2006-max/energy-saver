#!/usr/bin/env python3
"""
Full Backend API Testing for Energy Optimization SaaS
Tests all endpoints including authentication, onboarding, and full user flows.
"""

import requests
import sys
import json
import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class EnergyFullTester:
    def __init__(self, base_url: str = "https://energy-saver-16.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results: List[Dict[str, Any]] = []
        self.session_cookie = None
        self.session_data = None
        self.bill_id = None
        self.consumption_entry_id = None
        self.analysis_run_id = None
        self.report_id = None

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data if success else None
        })

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Any = None, files: Any = None, headers: Dict[str, str] = None, 
                 use_auth: bool = True) -> tuple[bool, Any]:
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            default_headers.pop('Content-Type', None)

        # Add session cookie if authenticated and use_auth is True
        cookies = {}
        if use_auth and self.session_cookie:
            cookies['energy_session'] = self.session_cookie

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, cookies=cookies, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, cookies=cookies, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=default_headers, cookies=cookies, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=default_headers, cookies=cookies, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, cookies=cookies, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            response_data = None
            
            if success:
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                except:
                    response_data = response.text
                    print(f"   Response (text): {response_data[:200]}...")
                    
                # Extract session cookie from Set-Cookie header if present
                if 'Set-Cookie' in response.headers and 'energy_session=' in response.headers['Set-Cookie']:
                    cookie_header = response.headers['Set-Cookie']
                    # Extract the session value
                    start = cookie_header.find('energy_session=') + len('energy_session=')
                    end = cookie_header.find(';', start)
                    if end == -1:
                        end = len(cookie_header)
                    self.session_cookie = cookie_header[start:end]
                    print(f"   Session cookie extracted")
            else:
                print(f"   Error: {response.text[:300]}")

            self.log_test(name, success, 
                         f"Expected {expected_status}, got {response.status_code}" if not success else "",
                         response_data)
            
            return success, response_data

        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"   {error_msg}")
            self.log_test(name, False, error_msg)
            return False, None

    def create_sample_pdf(self) -> bytes:
        """Create a sample PDF for testing"""
        return (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
            b"BT /F1 12 Tf 72 720 Td (Consumo 1240 kWh Totale EUR 348.90 Periodo 01/03/2026 31/03/2026) Tj ET\n"
            b"%%EOF"
        )

    def test_health_endpoint(self) -> bool:
        """Test GET /api/health"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200,
            use_auth=False
        )
        return success

    def test_dev_login(self) -> bool:
        """Test POST /api/auth/dev-login with test credentials"""
        payload = {
            "email": "demo@energysaver.app",
            "name": "Energy Saver Demo",
            "company_name": "Energy Saver Demo"
        }
        
        success, response = self.run_test(
            "Dev Bypass Login",
            "POST",
            "auth/dev-login",
            200,
            data=payload,
            use_auth=False
        )
        
        if success and isinstance(response, dict):
            if response.get("status") != "success":
                self.log_test("Dev Login - Status", False, f"Status not success: {response.get('status')}")
                return False
            
            session = response.get("session")
            if not session:
                self.log_test("Dev Login - Session", False, "No session in response")
                return False
                
            self.session_data = session
            print(f"   Logged in as: {session.get('user', {}).get('name')}")
            print(f"   Organization: {session.get('org', {}).get('name')}")
            print(f"   Site: {session.get('site', {}).get('name')}")
            
        return success

    def test_auth_me(self) -> bool:
        """Test GET /api/auth/me to verify session persistence"""
        success, response = self.run_test(
            "Auth Me - Session Check",
            "GET",
            "auth/me",
            200
        )
        
        if success and isinstance(response, dict):
            if not response.get("authenticated"):
                self.log_test("Auth Me - Authenticated", False, "Not authenticated")
                return False
                
        return success

    def test_google_oauth_start(self) -> bool:
        """Test GET /api/auth/google/start endpoint availability (without full flow)"""
        success, response = self.run_test(
            "Google OAuth Start Endpoint",
            "GET",
            "auth/google/start",
            302,  # Should redirect
            use_auth=False
        )
        return success

    def test_onboarding_state(self) -> bool:
        """Test GET /api/onboarding/state"""
        success, response = self.run_test(
            "Onboarding State",
            "GET",
            "onboarding/state",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ["org", "site"]
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log_test("Onboarding State - Fields", False, f"Missing fields: {missing_fields}")
                return False
                
        return success

    def test_onboarding_complete(self) -> bool:
        """Test POST /api/onboarding/complete"""
        payload = {
            "company_name": "Test Energy Company",
            "sector": "bar",
            "site_name": "Test Site Milano",
            "city": "Milano",
            "latitude": 45.4642,
            "longitude": 9.19,
            "business_open_hour": 8,
            "business_close_hour": 18,
            "savings_goal_pct": 15
        }
        
        success, response = self.run_test(
            "Onboarding Complete",
            "POST",
            "onboarding/complete",
            200,
            data=payload
        )
        
        if success and isinstance(response, dict):
            if response.get("status") != "success":
                self.log_test("Onboarding Complete - Status", False, f"Status not success: {response.get('status')}")
                return False
                
            session = response.get("session")
            if session:
                self.session_data = session
                
        return success

    def test_dashboard_overview(self) -> bool:
        """Test GET /api/dashboard/overview"""
        success, response = self.run_test(
            "Dashboard Overview",
            "GET",
            "dashboard/overview",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ["session", "integration_status", "counts"]
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log_test("Dashboard Overview - Fields", False, f"Missing fields: {missing_fields}")
                return False
                
            integration_status = response.get("integration_status", {})
            print(f"   Weather status: {integration_status.get('weather')}")
            print(f"   Price status: {integration_status.get('prices')}")
            print(f"   Email mode: {integration_status.get('email_mode')}")
            print(f"   Google OAuth configured: {integration_status.get('google_oauth_configured')}")
            
        return success

    def test_bill_upload(self) -> bool:
        """Test POST /api/bills/upload"""
        pdf_content = self.create_sample_pdf()
        
        files = {
            'file': ('test_bill.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        
        success, response = self.run_test(
            "Bill Upload",
            "POST",
            "bills/upload",
            200,
            files=files
        )
        
        if success and isinstance(response, dict):
            if response.get("status") != "success":
                self.log_test("Bill Upload - Status", False, f"Status not success: {response.get('status')}")
                return False
                
            bill = response.get("bill")
            if bill:
                self.bill_id = bill.get("id")
                print(f"   Bill uploaded with ID: {self.bill_id}")
                
        return success

    def test_bills_list(self) -> bool:
        """Test GET /api/bills"""
        success, response = self.run_test(
            "Bills List",
            "GET",
            "bills",
            200
        )
        
        if success and isinstance(response, dict):
            items = response.get("items", [])
            print(f"   Found {len(items)} bills")
            
        return success

    def test_bill_review(self) -> bool:
        """Test PATCH /api/bills/{bill_id} for manual correction"""
        if not self.bill_id:
            self.log_test("Bill Review", False, "No bill_id available")
            return False
            
        payload = {
            "consumption_kwh": 1500.0,
            "total_cost_eur": 420.50,
            "period_start": "01/03/2026",
            "period_end": "31/03/2026",
            "notes": "Manually reviewed and corrected"
        }
        
        success, response = self.run_test(
            "Bill Review/Correction",
            "PATCH",
            f"bills/{self.bill_id}",
            200,
            data=payload
        )
        
        if success and isinstance(response, dict):
            if response.get("status") != "success":
                self.log_test("Bill Review - Status", False, f"Status not success: {response.get('status')}")
                return False
                
        return success

    def test_consumption_single_entry(self) -> bool:
        """Test POST /api/consumption for single entry"""
        payload = {
            "timestamp": "2026-01-15T12:00:00Z",
            "kwh": 25.5,
            "cost_eur": 7.20,
            "note": "Test single consumption entry"
        }
        
        success, response = self.run_test(
            "Consumption Single Entry",
            "POST",
            "consumption",
            200,
            data=payload
        )
        
        if success and isinstance(response, dict):
            if response.get("status") != "success":
                self.log_test("Consumption Single - Status", False, f"Status not success: {response.get('status')}")
                return False
                
            entry = response.get("entry")
            if entry:
                self.consumption_entry_id = entry.get("id")
                print(f"   Consumption entry created with ID: {self.consumption_entry_id}")
                
        return success

    def test_consumption_batch_import(self) -> bool:
        """Test POST /api/consumption/batch for batch import"""
        entries = [
            {
                "timestamp": "2026-01-16T10:00:00Z",
                "kwh": 18.2,
                "cost_eur": 5.10,
                "note": "Batch entry 1"
            },
            {
                "timestamp": "2026-01-16T14:00:00Z",
                "kwh": 22.8,
                "cost_eur": 6.40,
                "note": "Batch entry 2"
            },
            {
                "timestamp": "2026-01-16T18:00:00Z",
                "kwh": 31.5,
                "cost_eur": 8.85,
                "note": "Batch entry 3"
            }
        ]
        
        payload = {"entries": entries}
        
        success, response = self.run_test(
            "Consumption Batch Import",
            "POST",
            "consumption/batch",
            200,
            data=payload
        )
        
        if success and isinstance(response, dict):
            if response.get("status") != "success":
                self.log_test("Consumption Batch - Status", False, f"Status not success: {response.get('status')}")
                return False
                
            count = response.get("count", 0)
            print(f"   Imported {count} consumption entries")
            
        return success

    def test_consumption_list(self) -> bool:
        """Test GET /api/consumption"""
        success, response = self.run_test(
            "Consumption List",
            "GET",
            "consumption",
            200
        )
        
        if success and isinstance(response, dict):
            items = response.get("items", [])
            print(f"   Found {len(items)} consumption entries")
            
        return success

    def test_analytics_run(self) -> bool:
        """Test POST /api/analytics/run"""
        success, response = self.run_test(
            "Analytics Run",
            "POST",
            "analytics/run",
            200
        )
        
        if success and isinstance(response, dict):
            if response.get("status") != "success":
                self.log_test("Analytics Run - Status", False, f"Status not success: {response.get('status')}")
                return False
                
            analysis_run = response.get("analysis_run")
            if analysis_run:
                self.analysis_run_id = analysis_run.get("id")
                analysis = analysis_run.get("analysis", {})
                
                # Verify analysis structure
                kpis = analysis.get("kpis", {})
                anomalies = analysis.get("anomalies", [])
                advices = analysis.get("advices", [])
                prediction = analysis.get("prediction", {})
                
                print(f"   Analysis run ID: {self.analysis_run_id}")
                print(f"   KPIs: {kpis.get('total_consumption_kwh')} kWh, €{kpis.get('total_cost_eur')}")
                print(f"   Found {len(anomalies)} anomalies, {len(advices)} advices")
                print(f"   Forecast: €{prediction.get('next_30_days_cost_eur')} next 30 days")
                
        return success

    def test_analytics_latest(self) -> bool:
        """Test GET /api/analytics/latest"""
        success, response = self.run_test(
            "Analytics Latest",
            "GET",
            "analytics/latest",
            200
        )
        
        if success and isinstance(response, dict):
            analysis_run = response.get("analysis_run")
            if analysis_run:
                print(f"   Latest analysis ID: {analysis_run.get('id')}")
                
        return success

    def test_notifications_list(self) -> bool:
        """Test GET /api/notifications"""
        success, response = self.run_test(
            "Notifications List",
            "GET",
            "notifications",
            200
        )
        
        if success and isinstance(response, dict):
            items = response.get("items", [])
            unread_count = response.get("unread_count", 0)
            print(f"   Found {len(items)} notifications, {unread_count} unread")
            
        return success

    def test_notifications_mark_read(self) -> bool:
        """Test POST /api/notifications/mark-all-read"""
        success, response = self.run_test(
            "Notifications Mark All Read",
            "POST",
            "notifications/mark-all-read",
            200
        )
        
        if success and isinstance(response, dict):
            if response.get("status") != "success":
                self.log_test("Notifications Mark Read - Status", False, f"Status not success: {response.get('status')}")
                return False
                
        return success

    def test_notification_preferences(self) -> bool:
        """Test GET and POST /api/notifications/preferences"""
        # First get current preferences
        success, response = self.run_test(
            "Notification Preferences Get",
            "GET",
            "notifications/preferences",
            200
        )
        
        if not success:
            return False
            
        # Then update preferences
        payload = {
            "email_enabled": True,
            "anomaly_alerts": True,
            "price_alerts": True,
            "report_alerts": False
        }
        
        success, response = self.run_test(
            "Notification Preferences Update",
            "POST",
            "notifications/preferences",
            200,
            data=payload
        )
        
        if success and isinstance(response, dict):
            if response.get("status") != "success":
                self.log_test("Notification Preferences Update - Status", False, f"Status not success: {response.get('status')}")
                return False
                
        return success

    def test_email_dev_mode(self) -> bool:
        """Test POST /api/notifications/test-email for dev mode email flow"""
        success, response = self.run_test(
            "Test Email Dev Mode",
            "POST",
            "notifications/test-email",
            200
        )
        
        if success and isinstance(response, dict):
            if response.get("status") != "success":
                self.log_test("Test Email - Status", False, f"Status not success: {response.get('status')}")
                return False
                
            message = response.get("message", "")
            if "sviluppo interna" not in message:
                self.log_test("Test Email - Dev Mode", False, f"Not dev mode message: {message}")
                return False
                
            print(f"   Email dev mode working: {message}")
            
        return success

    def test_reports_generate(self) -> bool:
        """Test POST /api/reports/generate"""
        success, response = self.run_test(
            "Reports Generate",
            "POST",
            "reports/generate",
            200
        )
        
        if success and isinstance(response, dict):
            if response.get("status") != "success":
                self.log_test("Reports Generate - Status", False, f"Status not success: {response.get('status')}")
                return False
                
            report = response.get("report")
            if report:
                self.report_id = report.get("id")
                print(f"   Report generated with ID: {self.report_id}")
                print(f"   Download path: {report.get('download_path')}")
                
        return success

    def test_reports_list(self) -> bool:
        """Test GET /api/reports"""
        success, response = self.run_test(
            "Reports List",
            "GET",
            "reports",
            200
        )
        
        if success and isinstance(response, dict):
            items = response.get("items", [])
            print(f"   Found {len(items)} reports")
            
        return success

    def test_reports_download(self) -> bool:
        """Test GET /api/reports/{report_id}/download"""
        if not self.report_id:
            self.log_test("Reports Download", False, "No report_id available")
            return False
            
        # Use requests directly for file download test
        url = f"{self.base_url}/api/reports/{self.report_id}/download"
        cookies = {}
        if self.session_cookie:
            cookies['energy_session'] = self.session_cookie
            
        try:
            response = requests.get(url, cookies=cookies, timeout=30)
            success = response.status_code == 200
            
            if success:
                content_type = response.headers.get('Content-Type', '')
                if 'application/pdf' not in content_type:
                    self.log_test("Reports Download - Content Type", False, f"Expected PDF, got: {content_type}")
                    return False
                    
                content_length = len(response.content)
                print(f"   Downloaded PDF report: {content_length} bytes")
                
            self.log_test("Reports Download", success, 
                         f"Expected 200, got {response.status_code}" if not success else "")
            
            return success
            
        except Exception as e:
            self.log_test("Reports Download", False, f"Exception: {str(e)}")
            return False

    def test_settings_summary(self) -> bool:
        """Test GET /api/settings/summary"""
        success, response = self.run_test(
            "Settings Summary",
            "GET",
            "settings/summary",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ["org", "site", "preferences", "integrations"]
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log_test("Settings Summary - Fields", False, f"Missing fields: {missing_fields}")
                return False
                
            integrations = response.get("integrations", {})
            print(f"   Weather provider: {integrations.get('weather_provider')}")
            print(f"   Price provider: {integrations.get('price_provider')}")
            print(f"   Google OAuth: {integrations.get('google_oauth')}")
            print(f"   Email mode: {integrations.get('email_mode')}")
            
        return success

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all full application tests"""
        print("🚀 Starting Energy Optimization SaaS Full Application Tests")
        print(f"   Base URL: {self.base_url}")
        print("=" * 80)
        
        # Test all endpoints in logical order
        tests = [
            # Basic health and auth
            self.test_health_endpoint,
            self.test_dev_login,
            self.test_auth_me,
            self.test_google_oauth_start,
            
            # Onboarding flow
            self.test_onboarding_state,
            self.test_onboarding_complete,
            
            # Dashboard
            self.test_dashboard_overview,
            
            # Bills management
            self.test_bill_upload,
            self.test_bills_list,
            self.test_bill_review,
            
            # Consumption management
            self.test_consumption_single_entry,
            self.test_consumption_batch_import,
            self.test_consumption_list,
            
            # Analytics
            self.test_analytics_run,
            self.test_analytics_latest,
            
            # Notifications
            self.test_notifications_list,
            self.test_notifications_mark_read,
            self.test_notification_preferences,
            self.test_email_dev_mode,
            
            # Reports
            self.test_reports_generate,
            self.test_reports_list,
            self.test_reports_download,
            
            # Settings
            self.test_settings_summary,
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test {test_func.__name__} crashed: {str(e)}")
                self.log_test(test_func.__name__, False, f"Test crashed: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests PASSED! Full application backend is working correctly.")
        else:
            print("⚠️  Some tests FAILED. Check the details above.")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": round((self.tests_passed / max(self.tests_run, 1)) * 100, 1),
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = EnergyFullTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["passed_tests"] == results["total_tests"] else 1

if __name__ == "__main__":
    sys.exit(main())