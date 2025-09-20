#!/usr/bin/env python3

import requests
import json
import time

def test_critical_fixes():
    print("🚨 TESTING CRITICAL FIXES")
    print("=========================")
    
    base_url = "http://localhost:8000"
    
    # Test 1: Gemini Integration
    print("1. Testing Gemini Integration...")
    try:
        response = requests.post(f"{base_url}/api/chat/general", data={"message": "What is 2+2?"})
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            if 'demo' in response_text.lower() or 'hello! i received' in response_text.lower():
                print("   ❌ GEMINI ISSUE: Still returning demo responses")
                print(f"   Response: {response_text[:100]}...")
                return False
            else:
                print("   ✅ GEMINI WORKING: Real AI responses")
                print(f"   Response: {response_text[:50]}...")
        else:
            print(f"   ❌ GEMINI FAILED: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ GEMINI ERROR: {e}")
        return False
    
    # Test 2: Authentication
    print("\n2. Testing Authentication...")
    try:
        # Login
        login_response = requests.post(f"{base_url}/api/auth/login", data={
            "email": "test@example.com",
            "password": "testpass123"
        })
        
        if login_response.status_code != 200:
            print(f"   ❌ LOGIN FAILED: HTTP {login_response.status_code}")
            return False
        
        token = login_response.json().get('access_token')
        if not token:
            print("   ❌ LOGIN FAILED: No token received")
            return False
        
        print(f"   ✅ LOGIN SUCCESS: Token {token[:20]}...")
        
        # Test upload with token
        test_content = b"Test document for critical fix verification"
        files = {'file': ('critical_test.txt', test_content, 'text/plain')}
        headers = {'Authorization': f'Bearer {token}'}
        
        upload_response = requests.post(f"{base_url}/api/content/upload", files=files, headers=headers)
        
        if upload_response.status_code == 200:
            print("   ✅ UPLOAD SUCCESS: Authentication working")
            return True
        else:
            print(f"   ❌ UPLOAD FAILED: HTTP {upload_response.status_code}")
            print(f"   Error: {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ AUTH ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_critical_fixes()
    print(f"\n🎯 CRITICAL FIXES RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
    if success:
        print("   Both Gemini integration and authentication are working!")
    else:
        print("   Critical issues still exist and need immediate attention.")


