#!/usr/bin/env python3
"""
Backend API Testing for Energy Optimization SaaS POC
Tests all core endpoints and integrations as specified in the review request.
"""

import requests
import sys
import json
import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class EnergyPOCTester:
    def __init__(self, base_url: str = "https://energy-saver-16.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results: List[Dict[str, Any]] = []
        self.dataset_id: Optional[str] = None
        self.analysis_id: Optional[str] = None

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
                 data: Any = None, files: Any = None, headers: Dict[str, str] = None) -> tuple[bool, Any]:
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            default_headers.pop('Content-Type', None)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=default_headers, timeout=30)
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
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ["status", "service", "timestamp"]
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log_test("Health Check - Fields", False, f"Missing fields: {missing_fields}")
                return False
            
            if response.get("status") != "ok":
                self.log_test("Health Check - Status", False, f"Status is not 'ok': {response.get('status')}")
                return False
                
        return success

    def test_contracts_endpoint(self) -> bool:
        """Test GET /api/poc/contracts"""
        success, response = self.run_test(
            "Contract Examples",
            "GET",
            "poc/contracts",
            200
        )
        
        if success and isinstance(response, dict):
            required_sections = ["manual_ingest", "analysis_output"]
            missing_sections = [section for section in required_sections if section not in response]
            if missing_sections:
                self.log_test("Contracts - Structure", False, f"Missing sections: {missing_sections}")
                return False
                
        return success

    def test_manual_ingest(self) -> bool:
        """Test POST /api/poc/ingest-manual with default generated sample readings"""
        payload = {
            "site_name": "Test PMI Site",
            "city": "Milano",
            "latitude": 45.4642,
            "longitude": 9.19
            # No readings provided - should use default generated sample
        }
        
        success, response = self.run_test(
            "Manual Ingest (Default Samples)",
            "POST",
            "poc/ingest-manual",
            200,
            data=payload
        )
        
        if success and isinstance(response, dict):
            required_fields = ["id", "created_at", "payload"]
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log_test("Manual Ingest - Response Fields", False, f"Missing fields: {missing_fields}")
                return False
            
            # Store dataset_id for later use
            self.dataset_id = response.get("id")
            
            # Check payload structure
            payload_data = response.get("payload", {})
            if "readings" not in payload_data:
                self.log_test("Manual Ingest - Readings", False, "No readings in payload")
                return False
                
            readings = payload_data.get("readings", [])
            if len(readings) == 0:
                self.log_test("Manual Ingest - Readings Count", False, "No readings generated")
                return False
                
            print(f"   Generated {len(readings)} sample readings")
            
        return success

    def test_upload_bill(self) -> bool:
        """Test POST /api/poc/upload-bill with PDF file and verify storage metadata + extraction_status"""
        pdf_content = self.create_sample_pdf()
        
        files = {
            'file': ('test_bill.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        
        success, response = self.run_test(
            "Upload Bill PDF",
            "POST",
            "poc/upload-bill",
            200,
            files=files
        )
        
        if success and isinstance(response, dict):
            required_fields = ["id", "filename", "storage_mode", "size_bytes", "uploaded_at", "extraction_status"]
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log_test("Upload Bill - Response Fields", False, f"Missing fields: {missing_fields}")
                return False
            
            # Verify extraction_status is valid
            extraction_status = response.get("extraction_status")
            valid_statuses = ["parsed", "needs_manual_review", "invalid_pdf"]
            if extraction_status not in valid_statuses:
                self.log_test("Upload Bill - Extraction Status", False, 
                             f"Invalid extraction_status: {extraction_status}")
                return False
            
            # Verify storage metadata
            if response.get("size_bytes") != len(pdf_content):
                self.log_test("Upload Bill - File Size", False, 
                             f"Size mismatch: expected {len(pdf_content)}, got {response.get('size_bytes')}")
                return False
                
            print(f"   File stored with extraction_status: {extraction_status}")
            
        return success

    def test_run_analysis(self) -> bool:
        """Test POST /api/poc/run-analysis and verify anomalies, advices, KPI and prediction are returned"""
        payload = {
            "site_name": "Test Analysis Site",
            "city": "Milano", 
            "latitude": 45.4642,
            "longitude": 9.19
            # No dataset_id or readings - should use default sample data
        }
        
        success, response = self.run_test(
            "Run POC Analysis",
            "POST",
            "poc/run-analysis",
            200,
            data=payload
        )
        
        if success and isinstance(response, dict):
            # Store analysis_id for later use
            self.analysis_id = response.get("id")
            
            # Check main response structure
            required_fields = ["id", "created_at", "weather_context", "price_signal_summary", "analysis"]
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log_test("Analysis - Response Fields", False, f"Missing fields: {missing_fields}")
                return False
            
            # Verify weather integration status
            weather_context = response.get("weather_context", {})
            weather_status = weather_context.get("status")
            if weather_status not in ["ok", "error"]:
                self.log_test("Analysis - Weather Status", False, f"Invalid weather status: {weather_status}")
                return False
            
            print(f"   Weather integration status: {weather_status}")
            
            # Verify price integration status  
            price_summary = response.get("price_signal_summary", {})
            price_status = price_summary.get("status")
            if price_status not in ["ok", "fallback", "error"]:
                self.log_test("Analysis - Price Status", False, f"Invalid price status: {price_status}")
                return False
                
            print(f"   Price integration status: {price_status}")
            
            # Verify analysis structure
            analysis = response.get("analysis", {})
            required_analysis_fields = ["kpis", "anomalies", "advices", "prediction", "signal_status"]
            missing_analysis_fields = [field for field in required_analysis_fields if field not in analysis]
            if missing_analysis_fields:
                self.log_test("Analysis - Analysis Fields", False, f"Missing analysis fields: {missing_analysis_fields}")
                return False
            
            # Verify KPIs
            kpis = analysis.get("kpis", {})
            required_kpi_fields = ["total_consumption_kwh", "total_cost_eur", "potential_monthly_savings_eur"]
            missing_kpi_fields = [field for field in required_kpi_fields if field not in kpis]
            if missing_kpi_fields:
                self.log_test("Analysis - KPI Fields", False, f"Missing KPI fields: {missing_kpi_fields}")
                return False
            
            # Verify anomalies (should be a list)
            anomalies = analysis.get("anomalies", [])
            if not isinstance(anomalies, list):
                self.log_test("Analysis - Anomalies Type", False, "Anomalies should be a list")
                return False
            
            # Verify advices (should be a list)
            advices = analysis.get("advices", [])
            if not isinstance(advices, list):
                self.log_test("Analysis - Advices Type", False, "Advices should be a list")
                return False
            
            # Verify prediction structure
            prediction = analysis.get("prediction", {})
            required_prediction_fields = ["next_30_days_cost_eur", "expected_variation_pct"]
            missing_prediction_fields = [field for field in required_prediction_fields if field not in prediction]
            if missing_prediction_fields:
                self.log_test("Analysis - Prediction Fields", False, f"Missing prediction fields: {missing_prediction_fields}")
                return False
            
            print(f"   Analysis generated: {len(anomalies)} anomalies, {len(advices)} advices")
            print(f"   KPIs: {kpis.get('total_consumption_kwh')} kWh, €{kpis.get('total_cost_eur')}")
            print(f"   Prediction: €{prediction.get('next_30_days_cost_eur')} next 30 days")
            
        return success

    def test_latest_analysis(self) -> bool:
        """Test GET /api/poc/latest-analysis returns the latest stored run"""
        success, response = self.run_test(
            "Latest Analysis",
            "GET",
            "poc/latest-analysis",
            200
        )
        
        if success and isinstance(response, dict):
            # Should have similar structure to run-analysis response
            required_fields = ["id", "created_at", "analysis"]
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log_test("Latest Analysis - Response Fields", False, f"Missing fields: {missing_fields}")
                return False
            
            # If we stored an analysis_id earlier, verify it matches
            if self.analysis_id and response.get("id") != self.analysis_id:
                print(f"   Warning: Latest analysis ID ({response.get('id')}) doesn't match last created ({self.analysis_id})")
            
            analysis = response.get("analysis", {})
            if "kpis" not in analysis:
                self.log_test("Latest Analysis - Analysis Structure", False, "Missing analysis.kpis")
                return False
                
        return success

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all POC backend tests"""
        print("🚀 Starting Energy Optimization SaaS POC Backend Tests")
        print(f"   Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test all endpoints in order
        tests = [
            self.test_health_endpoint,
            self.test_contracts_endpoint,
            self.test_manual_ingest,
            self.test_upload_bill,
            self.test_run_analysis,
            self.test_latest_analysis
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test {test_func.__name__} crashed: {str(e)}")
                self.log_test(test_func.__name__, False, f"Test crashed: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests PASSED! POC backend is working correctly.")
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
    tester = EnergyPOCTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["passed_tests"] == results["total_tests"] else 1

if __name__ == "__main__":
    sys.exit(main())