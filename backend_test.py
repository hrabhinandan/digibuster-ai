#!/usr/bin/env python3
"""
DigiBuster Backend API Test Suite
Tests all API endpoints for the technical support system
"""

import requests
import sys
import json
from datetime import datetime
import uuid

class DigiBusterAPITester:
    def __init__(self, base_url="https://ce3171a4-3bb3-4a04-bcf7-eeccecfa69c1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.customer_token = None
        self.agent_token = None
        self.customer_user = None
        self.agent_user = None
        self.test_ticket_id = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data
        timestamp = datetime.now().strftime('%H%M%S')
        self.customer_data = {
            "email": f"customer_{timestamp}@test.com",
            "password": "TestPass123!",
            "full_name": f"Test Customer {timestamp}",
            "role": "customer"
        }
        self.agent_data = {
            "email": f"agent_{timestamp}@test.com", 
            "password": "TestPass123!",
            "full_name": f"Test Agent {timestamp}",
            "role": "agent"
        }

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, token=None, expected_status=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}
                
            if expected_status and response.status_code != expected_status:
                return False, {
                    "error": f"Expected status {expected_status}, got {response.status_code}",
                    "response": response.text
                }
                
            try:
                return True, response.json()
            except:
                return True, {"status_code": response.status_code, "text": response.text}
                
        except Exception as e:
            return False, {"error": str(e)}

    def test_user_registration(self):
        """Test user registration for both customer and agent"""
        print("\n🔍 Testing User Registration...")
        
        # Test customer registration
        success, response = self.make_request(
            'POST', 'auth/register', 
            self.customer_data, 
            expected_status=200
        )
        
        if success and 'id' in response:
            self.customer_user = response
            self.log_test("Customer Registration", True, f"- User ID: {response['id']}")
        else:
            self.log_test("Customer Registration", False, f"- {response}")
            return False
            
        # Test agent registration  
        success, response = self.make_request(
            'POST', 'auth/register',
            self.agent_data,
            expected_status=200
        )
        
        if success and 'id' in response:
            self.agent_user = response
            self.log_test("Agent Registration", True, f"- User ID: {response['id']}")
            return True
        else:
            self.log_test("Agent Registration", False, f"- {response}")
            return False

    def test_user_login(self):
        """Test user login for both customer and agent"""
        print("\n🔍 Testing User Login...")
        
        # Test customer login
        login_data = {
            "email": self.customer_data["email"],
            "password": self.customer_data["password"]
        }
        
        success, response = self.make_request(
            'POST', 'auth/login',
            login_data,
            expected_status=200
        )
        
        if success and 'access_token' in response:
            self.customer_token = response['access_token']
            self.log_test("Customer Login", True, f"- Token received")
        else:
            self.log_test("Customer Login", False, f"- {response}")
            return False
            
        # Test agent login
        login_data = {
            "email": self.agent_data["email"], 
            "password": self.agent_data["password"]
        }
        
        success, response = self.make_request(
            'POST', 'auth/login',
            login_data,
            expected_status=200
        )
        
        if success and 'access_token' in response:
            self.agent_token = response['access_token']
            self.log_test("Agent Login", True, f"- Token received")
            return True
        else:
            self.log_test("Agent Login", False, f"- {response}")
            return False

    def test_auth_me(self):
        """Test getting current user info"""
        print("\n🔍 Testing Auth Me Endpoint...")
        
        # Test customer auth/me
        success, response = self.make_request(
            'GET', 'auth/me',
            token=self.customer_token,
            expected_status=200
        )
        
        if success and response.get('role') == 'customer':
            self.log_test("Customer Auth Me", True, f"- Role: {response['role']}")
        else:
            self.log_test("Customer Auth Me", False, f"- {response}")
            return False
            
        # Test agent auth/me
        success, response = self.make_request(
            'GET', 'auth/me',
            token=self.agent_token,
            expected_status=200
        )
        
        if success and response.get('role') == 'agent':
            self.log_test("Agent Auth Me", True, f"- Role: {response['role']}")
            return True
        else:
            self.log_test("Agent Auth Me", False, f"- {response}")
            return False

    def test_ticket_creation(self):
        """Test ticket creation by customer"""
        print("\n🔍 Testing Ticket Creation...")
        
        ticket_data = {
            "title": "Test Hardware Issue",
            "description": "My computer won't start properly. Need urgent help.",
            "category": "hardware",
            "priority": "high"
        }
        
        success, response = self.make_request(
            'POST', 'tickets',
            ticket_data,
            token=self.customer_token,
            expected_status=200
        )
        
        if success and 'id' in response:
            self.test_ticket_id = response['id']
            self.log_test("Ticket Creation", True, f"- Ticket ID: {response['id']}")
            return True
        else:
            self.log_test("Ticket Creation", False, f"- {response}")
            return False

    def test_ticket_access_control(self):
        """Test role-based access control for tickets"""
        print("\n🔍 Testing Ticket Access Control...")
        
        # Customer should only see their own tickets
        success, response = self.make_request(
            'GET', 'tickets',
            token=self.customer_token,
            expected_status=200
        )
        
        if success and isinstance(response, list):
            customer_tickets = len(response)
            self.log_test("Customer Ticket Access", True, f"- Can see {customer_tickets} tickets")
        else:
            self.log_test("Customer Ticket Access", False, f"- {response}")
            return False
            
        # Agent should see all tickets
        success, response = self.make_request(
            'GET', 'tickets',
            token=self.agent_token,
            expected_status=200
        )
        
        if success and isinstance(response, list):
            agent_tickets = len(response)
            self.log_test("Agent Ticket Access", True, f"- Can see {agent_tickets} tickets")
            
            # Agent should see at least as many tickets as customer
            if agent_tickets >= customer_tickets:
                self.log_test("Role-based Access Control", True, f"- Agent sees all tickets")
                return True
            else:
                self.log_test("Role-based Access Control", False, f"- Agent sees fewer tickets than expected")
                return False
        else:
            self.log_test("Agent Ticket Access", False, f"- {response}")
            return False

    def test_ticket_updates(self):
        """Test ticket status updates by agent"""
        print("\n🔍 Testing Ticket Updates...")
        
        if not self.test_ticket_id:
            self.log_test("Ticket Updates", False, "- No test ticket available")
            return False
            
        # Agent updates ticket status
        update_data = {
            "status": "in_progress",
            "agent_id": self.agent_user['id'],
            "agent_name": self.agent_user['full_name']
        }
        
        success, response = self.make_request(
            'PUT', f'tickets/{self.test_ticket_id}',
            update_data,
            token=self.agent_token,
            expected_status=200
        )
        
        if success and response.get('status') == 'in_progress':
            self.log_test("Agent Ticket Update", True, f"- Status updated to in_progress")
            
            # Test customer cannot update tickets
            customer_update = {"status": "resolved"}
            success, response = self.make_request(
                'PUT', f'tickets/{self.test_ticket_id}',
                customer_update,
                token=self.customer_token,
                expected_status=403
            )
            
            if not success or response.get('status_code') == 403:
                self.log_test("Customer Update Restriction", True, "- Customer correctly denied")
                return True
            else:
                self.log_test("Customer Update Restriction", False, "- Customer should not be able to update")
                return False
        else:
            self.log_test("Agent Ticket Update", False, f"- {response}")
            return False

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoints"""
        print("\n🔍 Testing Dashboard Statistics...")
        
        # Test customer stats
        success, response = self.make_request(
            'GET', 'dashboard/stats',
            token=self.customer_token,
            expected_status=200
        )
        
        if success and 'total_tickets' in response and response.get('role') == 'customer':
            self.log_test("Customer Dashboard Stats", True, f"- Total: {response['total_tickets']}")
        else:
            self.log_test("Customer Dashboard Stats", False, f"- {response}")
            return False
            
        # Test agent stats
        success, response = self.make_request(
            'GET', 'dashboard/stats',
            token=self.agent_token,
            expected_status=200
        )
        
        if success and 'total_tickets' in response and response.get('role') == 'agent':
            stats = response
            expected_keys = ['total_tickets', 'open_tickets', 'in_progress_tickets', 'resolved_tickets']
            if all(key in stats for key in expected_keys):
                self.log_test("Agent Dashboard Stats", True, f"- All stats present")
                return True
            else:
                self.log_test("Agent Dashboard Stats", False, f"- Missing stats keys")
                return False
        else:
            self.log_test("Agent Dashboard Stats", False, f"- {response}")
            return False

    def test_invalid_requests(self):
        """Test error handling for invalid requests"""
        print("\n🔍 Testing Error Handling...")
        
        # Test invalid login
        success, response = self.make_request(
            'POST', 'auth/login',
            {"email": "invalid@test.com", "password": "wrong"},
            expected_status=401
        )
        
        if not success or response.get('status_code') == 401:
            self.log_test("Invalid Login Handling", True, "- Correctly rejected")
        else:
            self.log_test("Invalid Login Handling", False, "- Should reject invalid credentials")
            return False
            
        # Test unauthorized access
        success, response = self.make_request(
            'GET', 'tickets',
            expected_status=401
        )
        
        if not success or response.get('status_code') == 401:
            self.log_test("Unauthorized Access Handling", True, "- Correctly rejected")
            return True
        else:
            self.log_test("Unauthorized Access Handling", False, "- Should require authentication")
            return False

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting DigiBuster API Test Suite")
        print(f"📡 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run tests in sequence
        test_methods = [
            self.test_user_registration,
            self.test_user_login,
            self.test_auth_me,
            self.test_ticket_creation,
            self.test_ticket_access_control,
            self.test_ticket_updates,
            self.test_dashboard_stats,
            self.test_invalid_requests
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ {test_method.__name__} - EXCEPTION: {str(e)}")
                
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 TEST RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Backend API is working correctly.")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed. Check the issues above.")
            return 1

def main():
    """Main test runner"""
    tester = DigiBusterAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())