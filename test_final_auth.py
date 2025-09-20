#!/usr/bin/env python3

import requests
import json
import time

def test_complete_auth_flow():
    print("🧪 COMPLETE AUTHENTICATION TEST")
    print("===============================")
    
    base_url = "http://localhost:8000"
    
    # Step 1: Register a new user
    print("1. Registering test user...")
    register_data = {
        'username': 'testuser_final',
        'email': 'test_final@example.com',
        'password': 'testpass123'
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/register", data=register_data)
        if response.status_code == 200:
            print("   ✅ Registration successful")
        elif response.status_code == 400 and "already exists" in response.text:
            print("   ⚠️  User already exists (expected)")
        else:
            print(f"   ❌ Registration failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
    
    # Step 2: Login
    print("2. Logging in...")
    login_data = {
        'email': 'test_final@example.com',
        'password': 'testpass123'
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", data=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"   ✅ Login successful, token: {token[:20]}...")
        else:
            print(f"   ❌ Login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False
    
    # Step 3: Test authenticated upload
    print("3. Testing authenticated upload...")
    headers = {'Authorization': f'Bearer {token}'}
    
    test_content = b"This is a final test document for authentication verification."
    files = {'file': ('final_test.txt', test_content, 'text/plain')}
    
    try:
        response = requests.post(f"{base_url}/api/content/upload", files=files, headers=headers)
        print(f"   Upload status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Upload successful: {data}")
            return True
        else:
            print(f"   ❌ Upload failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_auth_flow()
    print(f"\n🎯 FINAL RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
    if success:
        print("   Authentication and upload are working correctly!")
    else:
        print("   There are still issues that need to be fixed.")


