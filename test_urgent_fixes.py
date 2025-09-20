#!/usr/bin/env python3

import requests
import json
import time
import subprocess
import os

def start_backend():
    """Start the backend server"""
    print("🚀 Starting backend server...")
    try:
        # Start backend in background
        process = subprocess.Popen([
            'python', 'simple_main.py'
        ], cwd='backend', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(5)
        return process
    except Exception as e:
        print(f"Error starting backend: {e}")
        return None

def test_urgent_fixes():
    print("🚨 TESTING URGENT FIXES")
    print("=======================")
    
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
    
    # Test 2: Authentication
    print("\n2. Testing Authentication...")
    try:
        # Register user
        register_response = requests.post(f"{base_url}/api/auth/register", data={
            "username": "testuser_urgent",
            "email": "test_urgent@example.com",
            "password": "testpass123"
        })
        
        if register_response.status_code != 200:
            print(f"   ❌ Registration failed: {register_response.status_code}")
            return False
        
        # Login
        login_response = requests.post(f"{base_url}/api/auth/login", data={
            "email": "test_urgent@example.com",
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
        
        # Test upload with token
        test_content = b"Test document for urgent fix verification"
        files = {'file': ('urgent_test.txt', test_content, 'text/plain')}
        headers = {'Authorization': f'Bearer {token}'}
        
        upload_response = requests.post(f"{base_url}/api/content/upload", files=files, headers=headers)
        
        if upload_response.status_code == 200:
            print("   ✅ Upload working with authentication")
        else:
            print(f"   ❌ Upload failed: {upload_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False
    
    # Test 3: Gemini Integration
    print("\n3. Testing Gemini Integration...")
    try:
        response = requests.post(f"{base_url}/api/chat/general", data={"message": "What is 1+1?"}, timeout=10)
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
    
    return True

if __name__ == "__main__":
    # Start backend
    backend_process = start_backend()
    
    try:
        success = test_urgent_fixes()
        print(f"\n🎯 URGENT FIXES RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
        if success:
            print("   Both authentication and Gemini integration are working!")
        else:
            print("   Critical issues still exist and need immediate attention.")
    finally:
        # Clean up
        if backend_process:
            backend_process.terminate()
            print("\n🧹 Backend process terminated")


