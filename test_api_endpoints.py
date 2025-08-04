#!/usr/bin/env python3
"""
Test the actual HTTP API endpoints for bot improvements
"""

import requests
import json
from django.contrib.auth.models import User

# API Configuration
BASE_URL = "http://localhost:8000/api"

def test_api_with_requests():
    """Test the API endpoints using HTTP requests"""
    print("Testing bot improvement API endpoints via HTTP...")
    
    # We'll need a test bot user that exists
    # This assumes the bot user 'test_bot' was created by the previous test
    bot_username = "test_bot"
    
    # Test 1: Check if bot has commented on a post
    print(f"\n🧪 Test 1: Checking if {bot_username} has commented on post 1")
    
    url = f"{BASE_URL}/users/{bot_username}/post_comments/"
    params = {"post_id": 1}
    
    try:
        response = requests.get(url, params=params)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Django server not running")
        print("Start the server with: .venv/bin/python manage.py runserver")
        return
    
    # Test 2: Check pending replies for the bot
    print(f"\n🧪 Test 2: Checking pending replies for {bot_username}")
    
    url = f"{BASE_URL}/users/{bot_username}/pending_replies/"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Django server not running")
        return
    
    print("\n✅ API endpoint tests completed!")

if __name__ == '__main__':
    test_api_with_requests()
