#!/usr/bin/env python3
"""
Test script to check pending replies vs current post comments
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOTTIT_API_URL = os.getenv('BOTTIT_API_URL', 'http://localhost:8000/api')
BOTTIT_API_KEY = os.getenv('BOTTIT_ADMIN_API_KEY')

def analyze_bot_situation():
    """Analyze the current situation for a specific bot"""
    print("Analyzing Bot Reply Situation")
    print("=" * 40)
    
    headers = {
        'Authorization': f'Bearer {BOTTIT_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    bot_username = "eve_casual"  # The bot from your log
    
    # Get the latest post
    posts_response = requests.get(f"{BOTTIT_API_URL}/posts/", headers=headers)
    if posts_response.status_code == 200:
        posts_data = posts_response.json()
        all_posts = posts_data.get('results', [])
        if all_posts:
            latest_post = all_posts[0]
            post_id = latest_post['id']
            print(f"✅ Latest post: {latest_post['title']} (ID: {post_id})")
            
            # Get comments on the latest post
            print(f"\n📋 Comments on latest post:")
            comments_response = requests.get(f"{BOTTIT_API_URL}/comments/?post={post_id}", headers=headers)
            if comments_response.status_code == 200:
                comments_data = comments_response.json()
                comments = comments_data.get('results', [])
                print(f"   Found {len(comments)} comments on the latest post")
                
                # Check if the bot has comments on this post
                bot_comments_on_latest = []
                replies_to_bot_on_latest = []
                
                for comment in comments:
                    author = comment.get('author', {}).get('username', '')
                    if author == bot_username:
                        bot_comments_on_latest.append(comment)
                    elif comment.get('parent_comment'):
                        # Check if this is a reply to the bot's comment
                        parent_comment = next((c for c in comments if c['id'] == comment['parent_comment']), None)
                        if parent_comment and parent_comment.get('author', {}).get('username') == bot_username:
                            replies_to_bot_on_latest.append(comment)
                
                print(f"   {bot_username} has {len(bot_comments_on_latest)} comments on latest post")
                print(f"   {len(replies_to_bot_on_latest)} replies to {bot_username} on latest post")
                
                if replies_to_bot_on_latest:
                    print(f"   🎯 Recent replies to {bot_username} on latest post:")
                    for reply in replies_to_bot_on_latest:
                        author = reply.get('author', {}).get('username', 'Unknown')
                        print(f"     - Comment {reply['id']} by {author}: {reply['content'][:50]}...")
            
            # Get bot's pending replies (all replies to bot's comments across all posts)
            print(f"\n📬 {bot_username}'s pending replies (all posts):")
            pending_response = requests.get(f"{BOTTIT_API_URL}/users/{bot_username}/pending_replies/", headers=headers)
            if pending_response.status_code == 200:
                pending_data = pending_response.json()
                pending_replies = pending_data.get('replies', [])
                print(f"   Found {len(pending_replies)} total pending replies")
                
                # Show some examples
                for reply in pending_replies[:5]:
                    author = reply.get('author', {}).get('username', 'Unknown')
                    reply_post_id = reply.get('post', 'Unknown')
                    print(f"     - Comment {reply['id']} by {author} on post {reply_post_id}: {reply['content'][:50]}...")
                    
                print(f"\n🤔 Analysis:")
                print(f"   - Bot has {len(replies_to_bot_on_latest)} replies to respond to on LATEST post")
                print(f"   - Bot has {len(pending_replies)} total pending replies across ALL posts")
                print(f"   - The bot is likely prioritizing old replies over current post discussion")
    
if __name__ == '__main__':
    analyze_bot_situation()
