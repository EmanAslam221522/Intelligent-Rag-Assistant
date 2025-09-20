#!/usr/bin/env python3

import requests
import time
import subprocess
import os

def test_document_upload():
    print("🚨 TESTING DOCUMENT UPLOAD FIX")
    print("===============================")
    
    base_url = "http://localhost:8000"
    
    # Test 1: Backend Health
    print("1. Testing Backend Health...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend is healthy")
        else:
            print(f"   ❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend not responding: {e}")
        return False
    
    # Test 2: Simple LLM
    print("\n2. Testing Simple LLM...")
    try:
        response = requests.post(f"{base_url}/api/chat/general", data={"message": "What is 1+1?"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            print(f"   ✅ Simple LLM working: {response_text[:50]}...")
        else:
            print(f"   ❌ Simple LLM failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Simple LLM error: {e}")
        return False
    
    # Test 3: Authentication
    print("\n3. Testing Authentication...")
    try:
        # Register user
        register_response = requests.post(f"{base_url}/api/auth/register", data={
            "username": "testuser_doc",
            "email": "test_doc@example.com",
            "password": "testpass123"
        })
        
        if register_response.status_code != 200:
            print(f"   ❌ Registration failed: {register_response.status_code}")
            return False
        
        # Login
        login_response = requests.post(f"{base_url}/api/auth/login", data={
            "email": "test_doc@example.com",
            "password": "testpass123"
        })
        
        if login_response.status_code != 200:
            print(f"   ❌ Login failed: {login_response.status_code}")
            return False
        
        token = login_response.json().get('access_token')
        if not token:
            print("   ❌ No token received")
            return False
        
        print(f"   ✅ Authentication working, token: {token[:20]}...")
        
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False
    
    # Test 4: Document Upload
    print("\n4. Testing Document Upload...")
    try:
        # Create a test file
        test_content = "This is a test document for upload verification."
        files = {'file': ('test_document.txt', test_content, 'text/plain')}
        headers = {'Authorization': f'Bearer {token}'}
        
        upload_response = requests.post(f"{base_url}/api/content/upload", files=files, headers=headers)
        
        if upload_response.status_code == 200:
            data = upload_response.json()
            print(f"   ✅ Document upload working!")
            print(f"   File: {data.get('filename')}")
            print(f"   Size: {data.get('size')} bytes")
            print(f"   Content ID: {data.get('content_id')}")
            print(f"   Text length: {data.get('text_length')}")
        else:
            print(f"   ❌ Upload failed: {upload_response.status_code}")
            print(f"   Error: {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Upload test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_document_upload()
    print(f"\n🎯 DOCUMENT UPLOAD TEST: {'✅ SUCCESS' if success else '❌ FAILED'}")
    if success:
        print("   Document upload is now working!")
    else:
        print("   Document upload still has issues.")

