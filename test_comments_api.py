#!/usr/bin/env python3
"""
Test script to verify the comments API filtering works correctly
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOTTIT_API_URL = os.getenv('BOTTIT_API_URL', 'http://localhost:8000/api')
BOTTIT_API_KEY = os.getenv('BOTTIT_ADMIN_API_KEY')

def test_comments_api():
    """Test the comments API filtering by post"""
    print("Testing Comments API Filtering")
    print("=" * 40)
    
    headers = {
        'Authorization': f'Bearer {BOTTIT_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Get the latest post
    posts_response = requests.get(f"{BOTTIT_API_URL}/posts/", headers=headers)
    if posts_response.status_code == 200:
        posts_data = posts_response.json()
        all_posts = posts_data.get('results', [])
        if all_posts:
            latest_post = all_posts[0]
            post_id = latest_post['id']
            print(f"✅ Latest post found: {latest_post['title']} (ID: {post_id})")
            
            # Test method 1: Using query parameter
            print(f"\n🧪 Testing /comments/?post={post_id}")
            comments_response1 = requests.get(f"{BOTTIT_API_URL}/comments/?post={post_id}", headers=headers)
            print(f"   Status: {comments_response1.status_code}")
            if comments_response1.status_code == 200:
                comments_data1 = comments_response1.json()
                comments1 = comments_data1.get('results', [])
                print(f"   Found {len(comments1)} comments")
                for comment in comments1[:3]:  # Show first 3
                    print(f"     - Comment {comment['id']}: {comment['content'][:50]}...")
            else:
                print(f"   Error: {comments_response1.text}")
            
            # Test method 2: Using post comments endpoint
            print(f"\n🧪 Testing /posts/{post_id}/comments/")
            comments_response2 = requests.get(f"{BOTTIT_API_URL}/posts/{post_id}/comments/", headers=headers)
            print(f"   Status: {comments_response2.status_code}")
            if comments_response2.status_code == 200:
                comments2 = comments_response2.json()
                print(f"   Found {len(comments2)} comments")
                for comment in comments2[:3]:  # Show first 3
                    print(f"     - Comment {comment['id']}: {comment['content'][:50]}...")
            else:
                print(f"   Error: {comments_response2.text}")
                
            # Test method 3: Get all comments and filter manually (current broken approach)
            print(f"\n🧪 Testing /comments/ (get all and filter)")
            all_comments_response = requests.get(f"{BOTTIT_API_URL}/comments/", headers=headers)
            print(f"   Status: {all_comments_response.status_code}")
            if all_comments_response.status_code == 200:
                all_comments_data = all_comments_response.json()
                all_comments = all_comments_data.get('results', [])
                # Filter manually
                filtered_comments = [c for c in all_comments if c.get('post') == post_id]
                print(f"   Found {len(all_comments)} total comments, {len(filtered_comments)} for post {post_id}")
                for comment in filtered_comments[:3]:  # Show first 3
                    print(f"     - Comment {comment['id']}: {comment['content'][:50]}...")
            else:
                print(f"   Error: {all_comments_response.text}")
        else:
            print("❌ No posts found")
    else:
        print(f"❌ Failed to get posts: {posts_response.text}")

if __name__ == '__main__':
    test_comments_api()
