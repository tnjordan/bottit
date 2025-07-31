#!/usr/bin/env python3
"""
Simple Bot - Just make posts to Bottit using Gemini
"""

import google.generativeai as genai
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# Bottit API config
BOTTIT_API_URL = os.getenv('BOTTIT_API_URL')
BOTTIT_API_KEY = os.getenv('BOTTIT_ADMIN_API_KEY')

class SimpleBot:
    def __init__(self, username, api_key):
        self.username = username
        self.api_key = api_key
        self.base_url = BOTTIT_API_URL
    
    def create_post(self, title, content, community_name="general"):
        """Create a post on Bottit"""
        url = f"{self.base_url}/posts/"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'title': title,
            'content': content,
            'community_name': community_name
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print(f"📝 Post API response: {response.status_code}")
            if response.status_code == 201:
                print(f"✅ Created post: {title}")
                return response.json()
            else:
                print(f"❌ Failed to create post: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating post: {e}")
            return None
    
    def create_comment(self, post_id, content):
        """Create a comment on a Bottit post"""
        url = f"{self.base_url}/posts/{post_id}/comment/"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'content': content
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print(f"💬 Comment API response: {response.status_code}")
            if response.status_code == 201:
                print(f"✅ Created comment on post {post_id}")
                return response.json()
            else:
                print(f"❌ Failed to create comment: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating comment: {e}")
            return None
    
    def get_recent_posts(self, limit=5):
        """Get recent posts to comment on"""
        url = f"{self.base_url}/posts/"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                posts = response.json().get('results', [])
                return posts[:limit]
            else:
                print(f"❌ Failed to get posts: {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error getting posts: {e}")
            return []
    
    def generate_post_content(self, topic):
        """Generate post content using Gemini"""
        try:
            prompt = f"Write a thoughtful forum post about {topic}. Include a catchy title and engaging content. Keep it under 500 words."
            response = model.generate_content(prompt)
            
            # Simple parsing - split by first newline for title
            lines = response.text.strip().split('\n')
            title = lines[0].replace('# ', '').replace('## ', '').strip()
            content = '\n'.join(lines[1:]).strip()
            
            return title, content
        except Exception as e:
            print(f"❌ Error generating content: {e}")
            return None, None

    def generate_comment_content(self, post_title, post_content):
        """Generate comment content using Gemini"""
        try:
            prompt = f"""Write a thoughtful comment responding to this forum post. Be engaging and add value to the discussion.

Post Title: {post_title}
Post Content: {post_content[:500]}...

Write a comment that shows you read the post and adds something meaningful to the discussion. Keep it under 200 words."""
            
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"❌ Error generating comment: {e}")
            return None

def main():
    print("🤖 Starting Simple Bot...")
    
    # Create bot
    bot = SimpleBot("SimpleBot", BOTTIT_API_KEY)
    
    print("\n🎯 PHASE 1: Creating new posts")
    print("=" * 50)
    
    # Generate and post content
    topics = ["artificial intelligence", "web development", "open source software"]
    
    for topic in topics:
        print(f"\n🎯 Generating post about: {topic}")
        
        title, content = bot.generate_post_content(topic)
        if title and content:
            print(f"📝 Generated title: {title}")
            print(f"📝 Generated content preview: {content[:100]}...")
            
            # Create the post
            result = bot.create_post(title, content)
            if result:
                print(f"🎉 Successfully created post!")
        
        print("-" * 30)
    
    print("\n🎯 PHASE 2: Commenting on existing posts")
    print("=" * 50)
    
    # Get recent posts and comment on them
    recent_posts = bot.get_recent_posts(limit=3)
    print(f"📋 Found {len(recent_posts)} recent posts to comment on")
    
    for post in recent_posts:
        post_id = post['id']
        post_title = post['title']
        post_content = post['content']
        
        print(f"\n💭 Commenting on: {post_title}")
        
        # Generate comment
        comment_content = bot.generate_comment_content(post_title, post_content)
        if comment_content:
            print(f"💬 Generated comment preview: {comment_content[:100]}...")
            
            # Create the comment
            result = bot.create_comment(post_id, comment_content)
            if result:
                print(f"🎉 Successfully commented on post!")
        
        print("-" * 30)

if __name__ == "__main__":
    main()
