#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class EnergyOptimizerTester:
    def __init__(self, base_url="https://energy-saver-16.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", error=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {error}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "error": error
        })

    def test_health_check(self):
        """Test basic health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            success = response.status_code == 200
            self.log_test("Health Check", success, 
                         f"Status: {response.status_code}" if success else "",
                         f"Status: {response.status_code}" if not success else "")
            return success
        except Exception as e:
            self.log_test("Health Check", False, error=str(e))
            return False

    def test_dev_login(self):
        """Test dev bypass login"""
        try:
            payload = {
                "email": "demo@energysaver.app",
                "name": "Energy Saver Demo",
                "company_name": "Energy Saver Demo"
            }
            response = self.session.post(f"{self.base_url}/api/auth/dev-login", 
                                       json=payload, timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("status") == "success" and "session" in data
            
            self.log_test("Dev Bypass Login", success,
                         "Login successful, session created" if success else "",
                         f"Status: {response.status_code}, Response: {response.text[:200]}" if not success else "")
            return success
        except Exception as e:
            self.log_test("Dev Bypass Login", False, error=str(e))
            return False

    def test_auth_me(self):
        """Test session validation"""
        try:
            response = self.session.get(f"{self.base_url}/api/auth/me", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("authenticated") == True and "session" in data
            
            self.log_test("Session Validation", success,
                         "Session valid and authenticated" if success else "",
                         f"Status: {response.status_code}" if not success else "")
            return success
        except Exception as e:
            self.log_test("Session Validation", False, error=str(e))
            return False

    def upload_test_pdf(self, filename="test_bill.pdf"):
        """Upload a test PDF that should land in needs_manual_review"""
        try:
            # Create a test PDF that will trigger needs_manual_review
            pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nBT /F1 12 Tf 72 720 Td (Test Bill - No clear consumption or cost data) Tj ET\n%%EOF"
            
            files = {'file': (filename, pdf_content, 'application/pdf')}
            response = self.session.post(f"{self.base_url}/api/bills/upload", 
                                       files=files, timeout=15)
            
            success = response.status_code == 200
            bill_id = None
            extraction_status = None
            
            if success:
                data = response.json()
                success = data.get("status") == "success" and "bill" in data
                if success:
                    bill_id = data["bill"]["id"]
                    extraction_status = data["bill"]["extraction_status"]
            
            self.log_test("Upload PDF (needs review)", success,
                         f"Bill ID: {bill_id}, Status: {extraction_status}" if success else "",
                         f"Status: {response.status_code}, Response: {response.text[:200]}" if not success else "")
            
            return success, bill_id, extraction_status
        except Exception as e:
            self.log_test("Upload PDF (needs review)", False, error=str(e))
            return False, None, None

    def test_analytics_blocked_with_unreviewed_bills(self):
        """Test that analytics is blocked when only bills with needs_manual_review exist"""
        try:
            response = self.session.post(f"{self.base_url}/api/analytics/run", timeout=20)
            
            # Should return 400 with explicit error message about pending reviews
            success = response.status_code == 400
            error_message = ""
            
            if response.status_code == 400:
                try:
                    data = response.json()
                    error_message = data.get("detail", "")
                    # Check if error message mentions bill review requirement
                    success = "rivedere" in error_message.lower() or "review" in error_message.lower()
                except:
                    success = False
            
            self.log_test("Analytics Blocked (unreviewed bills)", success,
                         f"Correctly blocked with message: {error_message}" if success else "",
                         f"Expected 400 with review message, got {response.status_code}: {response.text[:200]}" if not success else "")
            
            return success
        except Exception as e:
            self.log_test("Analytics Blocked (unreviewed bills)", False, error=str(e))
            return False

    def complete_bill_review(self, bill_id):
        """Complete bill review with valid data"""
        try:
            review_data = {
                "consumption_kwh": 1240.5,
                "total_cost_eur": 348.90,
                "period_start": "01/03/2026",
                "period_end": "31/03/2026",
                "notes": "Test review completion"
            }
            
            response = self.session.patch(f"{self.base_url}/api/bills/{bill_id}", 
                                        json=review_data, timeout=10)
            
            success = response.status_code == 200
            new_status = None
            
            if success:
                data = response.json()
                success = data.get("status") == "success" and "bill" in data
                if success:
                    new_status = data["bill"]["extraction_status"]
                    success = new_status == "parsed"
            
            self.log_test("Complete Bill Review", success,
                         f"Status changed to: {new_status}" if success else "",
                         f"Status: {response.status_code}, Response: {response.text[:200]}" if not success else "")
            
            return success
        except Exception as e:
            self.log_test("Complete Bill Review", False, error=str(e))
            return False

    def test_analytics_succeeds_after_review(self):
        """Test that analytics succeeds after bill review completion"""
        try:
            response = self.session.post(f"{self.base_url}/api/analytics/run", timeout=30)
            
            success = response.status_code == 200
            analysis_data = None
            
            if success:
                data = response.json()
                success = data.get("status") == "success" and "analysis_run" in data
                if success:
                    analysis_data = data["analysis_run"]
            
            self.log_test("Analytics Success (after review)", success,
                         f"Analysis completed with {len(analysis_data.get('analysis', {}).get('advices', []))} advices" if success and analysis_data else "",
                         f"Status: {response.status_code}, Response: {response.text[:200]}" if not success else "")
            
            return success
        except Exception as e:
            self.log_test("Analytics Success (after review)", False, error=str(e))
            return False

    def test_dashboard_warning_for_pending_reviews(self):
        """Test dashboard shows warning for pending bill reviews"""
        try:
            # First upload another bill that needs review
            pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nBT /F1 12 Tf 72 720 Td (Another test bill needing review) Tj ET\n%%EOF"
            files = {'file': ('pending_bill.pdf', pdf_content, 'application/pdf')}
            upload_response = self.session.post(f"{self.base_url}/api/bills/upload", files=files, timeout=15)
            
            if upload_response.status_code != 200:
                self.log_test("Dashboard Warning (pending reviews)", False, 
                             error="Failed to upload test bill for pending review test")
                return False
            
            # Now check dashboard
            response = self.session.get(f"{self.base_url}/api/dashboard/overview", timeout=10)
            
            success = response.status_code == 200
            pending_count = 0
            
            if success:
                data = response.json()
                pending_count = data.get("counts", {}).get("pending_bill_reviews", 0)
                success = pending_count > 0
            
            self.log_test("Dashboard Warning (pending reviews)", success,
                         f"Found {pending_count} pending bill reviews" if success else "",
                         f"Status: {response.status_code}, No pending reviews found" if not success else "")
            
            return success
        except Exception as e:
            self.log_test("Dashboard Warning (pending reviews)", False, error=str(e))
            return False

    def test_session_persistence_across_requests(self):
        """Test that dev login session persists across multiple requests"""
        try:
            # Make multiple authenticated requests to verify session persistence
            endpoints = ["/api/auth/me", "/api/dashboard/overview", "/api/bills"]
            all_success = True
            
            for endpoint in endpoints:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code != 200:
                    all_success = False
                    break
                # Small delay to simulate navigation
                time.sleep(0.1)
            
            self.log_test("Session Persistence", all_success,
                         "Session maintained across multiple requests" if all_success else "",
                         "Session lost during request sequence" if not all_success else "")
            
            return all_success
        except Exception as e:
            self.log_test("Session Persistence", False, error=str(e))
            return False

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Energy Optimization SaaS V1 Bug Fix Verification")
        print("=" * 70)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed, stopping tests")
            return False
        
        # Authentication flow with retry logic
        if not self.test_dev_login():
            print("❌ Dev login failed, stopping tests")
            return False
        
        # Verify session is working
        if not self.test_auth_me():
            print("❌ Session validation failed, stopping tests")
            return False
        
        # Test session persistence
        self.test_session_persistence_across_requests()
        
        # Test the main bug fix: analytics should be blocked with unreviewed bills
        print("\n📋 Testing analytics blocking with unreviewed bills...")
        
        # Upload a PDF that will need manual review
        upload_success, bill_id, extraction_status = self.upload_test_pdf()
        if not upload_success:
            print("❌ PDF upload failed, cannot test analytics blocking")
            return False
        
        if extraction_status != "needs_manual_review":
            print(f"⚠️  Expected 'needs_manual_review', got '{extraction_status}' - may affect test validity")
        
        # Test that analytics is properly blocked
        analytics_blocked = self.test_analytics_blocked_with_unreviewed_bills()
        
        # Complete the bill review
        if bill_id:
            review_success = self.complete_bill_review(bill_id)
            if review_success:
                # Test that analytics now succeeds
                self.test_analytics_succeeds_after_review()
        
        # Test dashboard warning functionality
        self.test_dashboard_warning_for_pending_reviews()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Bug fixes verified successfully.")
            return True
        else:
            print("⚠️  Some tests failed. Review the issues above.")
            return False

def main():
    tester = EnergyOptimizerTester()
    success = tester.run_comprehensive_test()
    
    # Save detailed results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": f"{(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%",
        "test_details": tester.test_results
    }
    
    with open("/app/test_reports/backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())