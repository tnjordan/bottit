#!/usr/bin/env python3
"""
Test script to verify bots only work on the most recent post
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot_farm'))

from bot_farm.organizer import BotFarmOrganizer, BotConfig
from bot_farm.personalities import BotPersonalityType

def test_recent_post_focus():
    """Test that bots only focus on the most recent post"""
    print("🧪 Testing bot focus on most recent post...")
    
    # Create organizer
    organizer = BotFarmOrganizer()
    
    # Add a test bot
    test_bot = BotConfig(
        bot_id="test_bot",
        personality_type=BotPersonalityType.ENTHUSIAST,
        api_key="test_key"
    )
    
    if organizer.add_bot(test_bot):
        print("✅ Test bot added successfully")
    else:
        print("❌ Failed to add test bot")
        return
    
    # Test fetch_available_content method
    print("\n📋 Testing content fetching...")
    posts, comments = organizer.fetch_available_content()
    
    print(f"Posts fetched: {len(posts)}")
    print(f"Comments fetched: {len(comments)}")
    
    if posts:
        print(f"Latest post: {posts[0].get('title', 'Unknown')}")
        print(f"Post ID: {posts[0].get('id')}")
        
        # Verify only one post is returned
        if len(posts) == 1:
            print("✅ Only one (most recent) post fetched - CORRECT")
        else:
            print("❌ Multiple posts fetched - this should not happen")
    else:
        print("⚠️ No posts available")
    
    if comments:
        print(f"Comments are for post: {comments[0].get('post') if comments else 'N/A'}")
        # Verify all comments are for the same post
        post_ids = set(comment.get('post') for comment in comments)
        if len(post_ids) <= 1:
            print("✅ All comments are for the same post - CORRECT")
        else:
            print(f"❌ Comments from multiple posts: {post_ids}")
    
    # Test bot cycle
    print("\n🤖 Testing bot cycle...")
    if posts:
        bot_id = list(organizer.bots.keys())[0]
        result = organizer.run_bot_cycle(bot_id, posts, comments)
        print(f"Bot cycle result: {result}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_recent_post_focus()
