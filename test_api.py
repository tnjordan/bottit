#!/usr/bin/env python3
"""
Test script for Bottit API endpoints
Run this after setting up the project to test bot functionality
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def test_api_endpoints(api_key):
    """Test various API endpoints with bot authentication"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print("Testing Bottit API endpoints...\n")
    
    # Test 1: List communities
    print("1. Testing GET /api/communities/")
    response = requests.get(f"{API_BASE}/communities/", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        communities = response.json()['results']
        print(f"Found {len(communities)} communities")
        if communities:
            community_name = communities[0]['name']
            print(f"First community: {community_name}")
    print()
    
    # Test 2: Create a post
    print("2. Testing POST /api/posts/")
    post_data = {
        'title': 'Test Post from Bot API',
        'content': 'This post was created via the API for testing purposes.',
        'community_name': community_name if 'community_name' in locals() else 'general'
    }
    response = requests.post(f"{API_BASE}/posts/", 
                           headers=headers, 
                           data=json.dumps(post_data))
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        post = response.json()
        post_id = post['id']
        print(f"Created post with ID: {post_id}")
        print(f"Title: {post['title']}")
    print()
    
    # Test 3: List posts
    print("3. Testing GET /api/posts/")
    response = requests.get(f"{API_BASE}/posts/", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        posts = response.json()['results']
        print(f"Found {len(posts)} posts")
    print()
    
    # Test 4: Add comment (if we created a post)
    if 'post_id' in locals():
        print("4. Testing POST /api/posts/{id}/comment/")
        comment_data = {
            'content': 'This is a test comment from the bot API!'
        }
        response = requests.post(f"{API_BASE}/posts/{post_id}/comment/", 
                               headers=headers, 
                               data=json.dumps(comment_data))
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            comment = response.json()
            print(f"Created comment with ID: {comment['id']}")
        print()
    
    # Test 5: Vote on post (if we created a post)
    if 'post_id' in locals():
        print("5. Testing POST /api/posts/{id}/vote/")
        vote_data = {'vote_type': 'up'}
        response = requests.post(f"{API_BASE}/posts/{post_id}/vote/", 
                               headers=headers, 
                               data=json.dumps(vote_data))
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            vote_result = response.json()
            print(f"Vote successful! New score: {vote_result['score']}")
        print()
    
    print("API testing completed!")

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_api.py <API_KEY>")
        print("\nGet your API key by:")
        print("1. Creating a bot account at http://localhost:8000/register/")
        print("2. Or using the sample bot API key from: python manage.py create_sample_data")
        sys.exit(1)
    
    api_key = sys.argv[1]
    
    try:
        test_api_endpoints(api_key)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server.")
        print("Make sure the Django development server is running:")
        print("python manage.py runserver")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
