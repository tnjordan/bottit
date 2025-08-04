#!/usr/bin/env python3
"""
Debug bot behavior - run a single cycle to see what's happening
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append('/home/todd/gt/bottit')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bottit.settings')
django.setup()

from bot_farm.organizer import BotFarmOrganizer, BotConfig
from bot_farm.personalities import BotPersonalityType


def debug_bot_cycle():
    """Run a single bot cycle with detailed debugging"""
    print("🔧 Debug: Starting bot cycle test...")
    
    # Set up organizer with test configuration
    organizer = BotFarmOrganizer(base_url="http://localhost:8000/api")
    
    # Add a test bot
    test_config = BotConfig(
        bot_id="debug_bot",
        personality_type=BotPersonalityType.ENTHUSIAST,
        api_key="test_key"  # This won't work for real API calls but good for debugging
    )
    
    if organizer.add_bot(test_config):
        print("✅ Bot added successfully")
    else:
        print("❌ Failed to add bot")
        return
    
    # Fetch available content (this will fail without server but we can see the structure)
    print("\n🔍 Fetching available content...")
    try:
        content = organizer.fetch_available_content()
        print(f"Posts: {len(content['posts'])}")
        print(f"Comments: {len(content['comments'])}")
        
        if content['posts']:
            post = content['posts'][0]
            print(f"Latest post: '{post.get('title', 'No title')}' (ID: {post.get('id')})")
        
        if content['comments']:
            print(f"Sample comments:")
            for i, comment in enumerate(content['comments'][:3]):
                author = comment.get('author', {}).get('username', 'Unknown')
                content_preview = comment.get('content', '')[:50] + '...' if len(comment.get('content', '')) > 50 else comment.get('content', '')
                print(f"  {i+1}. {author}: {content_preview}")
        
    except Exception as e:
        print(f"❌ Failed to fetch content: {e}")
        print("This is expected if the Django server isn't running")
        
        # Create mock data for testing
        content = {
            'posts': [{
                'id': 1,
                'title': 'Test Post',
                'content': 'This is a test post',
                'author': {'username': 'test_user'}
            }],
            'comments': [{
                'id': 1,
                'content': 'This is a test comment',
                'author': {'username': 'another_user'},
                'post': 1,
                'parent_comment': None
            }]
        }
    
    # Test bot decision making
    print("\n🧠 Testing bot decision making...")
    bot = organizer.bots["debug_bot"]
    
    try:
        action = bot.decide_action(content['posts'], content['comments'])
        if action:
            print(f"✅ Bot decided on action: {action.action_type}")
            print(f"   Target ID: {action.target_id}")
            print(f"   Content: {action.content}")
            print(f"   Vote type: {action.vote_type}")
        else:
            print("❌ Bot decided not to take any action")
    except Exception as e:
        print(f"❌ Error in bot decision making: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    debug_bot_cycle()
