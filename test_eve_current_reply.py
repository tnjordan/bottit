#!/usr/bin/env python3
"""
Test eve_casual specifically to see if she prioritizes the current post reply
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_farm.bot_framework import BotFramework
from bot_farm.organizer import BotFarmOrganizer
from bot_farm.personalities import get_personality, BotPersonalityType

def test_eve_current_reply():
    print("🧪 Testing eve_casual's decision making with current post reply...")
    
    # Create organizer and fetch content
    organizer = BotFarmOrganizer()
    available_posts, available_comments = organizer.fetch_available_content()
    
    print(f"Available posts: {len(available_posts)}")
    print(f"Available comments: {len(available_comments)}")
    
    if available_posts:
        current_post = available_posts[0]
        print(f"Current post: '{current_post['title']}' (ID: {current_post['id']})")
    
    # Create eve_casual bot
    eve_personality = get_personality(BotPersonalityType.CASUAL)
    eve_bot = BotFramework('eve_casual', eve_personality)
    
    # Get eve's pending replies
    pending_replies = eve_bot.get_pending_replies()
    print(f"\n📬 eve_casual has {len(pending_replies)} total pending replies")
    
    # Check for current post replies
    current_post_replies = []
    if available_posts:
        current_post_id = available_posts[0]['id']
        for reply in pending_replies:
            if reply.get('post') == current_post_id:
                reply_author = reply.get('author', {}).get('username')
                if reply_author != 'eve_casual':
                    current_post_replies.append(reply)
    
    print(f"🔥 eve_casual has {len(current_post_replies)} replies on current post (ID: {current_post_id})")
    
    if current_post_replies:
        for reply in current_post_replies:
            author = reply.get('author', {}).get('username', 'unknown')
            content = reply.get('content', '')[:50] + '...' if len(reply.get('content', '')) > 50 else reply.get('content', '')
            print(f"   Reply from {author}: {content}")
    
    # Test bot decision making
    print(f"\n🧠 Testing eve_casual's decision making...")
    for i in range(5):
        action = eve_bot.decide_action(available_posts, available_comments)
        print(f"  Attempt {i+1}: {action.action_type} -> {action}")

if __name__ == "__main__":
    test_eve_current_reply()
