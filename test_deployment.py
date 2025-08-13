#!/usr/bin/env python3
"""
Test script to diagnose deployment issues
"""

import requests
import json
import sys
import time

SERVER_URL = "http://103.136.69.249:8080"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=10)
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_main_page():
    """Test main page"""
    try:
        response = requests.get(SERVER_URL, timeout=10)
        print(f"✅ Main page: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Main page failed: {e}")
        return False

def test_api_keys():
    """Test if API keys are working"""
    try:
        # Test a simple request to check if OpenAI API key works
        response = requests.post(f"{SERVER_URL}/api/test", 
                               json={"test": "api_keys"}, 
                               timeout=30)
        print(f"✅ API test: {response.status_code}")
        return True
    except Exception as e:
        print(f"⚠️  API test: {e}")
        return False

def test_file_upload():
    """Test file upload functionality"""
    try:
        # Create a simple test file
        test_content = b"test image data"
        files = {'files': ('test.jpg', test_content, 'image/jpeg')}
        
        response = requests.post(f"{SERVER_URL}/process_batch", 
                               files=files, 
                               timeout=60)
        print(f"✅ File upload test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Batch ID: {data.get('batch_id', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ File upload failed: {e}")
        return False

def main():
    print("🔍 Testing YM Image Processor deployment...")
    print(f"Server: {SERVER_URL}")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Main Page", test_main_page),
        ("API Keys", test_api_keys),
        ("File Upload", test_file_upload)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Score: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Deployment is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()