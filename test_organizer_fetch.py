#!/usr/bin/env python3
"""
Test script to verify the organizer's fetch_available_content method
"""

import os
import sys
sys.path.append('/home/todd/gt/bottit')

from bot_farm.organizer import BotFarmOrganizer

def test_organizer_fetch():
    """Test the organizer's content fetching"""
    print("Testing Organizer Content Fetching")
    print("=" * 40)
    
    organizer = BotFarmOrganizer()
    
    # Test the fetch_available_content method
    content = organizer.fetch_available_content()
    
    print(f"✅ Posts found: {len(content.get('posts', []))}")
    for post in content.get('posts', []):
        print(f"   - Post {post['id']}: {post['title']}")
    
    print(f"✅ Comments found: {len(content.get('comments', []))}")
    for comment in content.get('comments', [])[:5]:  # Show first 5
        author = comment.get('author', {}).get('username', 'Unknown')
        print(f"   - Comment {comment['id']} by {author}: {comment['content'][:50]}...")

if __name__ == '__main__':
    test_organizer_fetch()
