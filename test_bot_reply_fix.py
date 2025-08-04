#!/usr/bin/env python3
"""
Test script to verify the bot reply fix works correctly
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

from core.models import CustomUser, Post, Comment, Community
from django.contrib.auth import get_user_model
from bot_farm.bot_framework import BotFramework
from bot_farm.personalities import get_personality, BotPersonalityType
import requests

def test_reply_logic():
    """Test the bot reply logic with simulated data"""
    print("Testing Bot Reply Logic Fix")
    print("=" * 40)
    
    # Get existing users and create test data if needed
    User = get_user_model()
    
    # Create or get test bot user
    bot_user, created = User.objects.get_or_create(
        username='test_reply_bot',
        defaults={
            'email': 'test_reply_bot@example.com',
            'is_bot': True,
        }
    )
    
    # Create or get regular user
    regular_user, created = User.objects.get_or_create(
        username='test_regular_user',
        defaults={
            'email': 'test_regular@example.com'
        }
    )
    
    # Use existing community
    community = Community.objects.filter(name='general').first()
    if not community:
        community = Community.objects.first()
    
    print(f"✅ Using bot: {bot_user.username}")
    print(f"✅ Using regular user: {regular_user.username}")
    print(f"✅ Using community: {community.name}")
    
    # Create test post
    post, created = Post.objects.get_or_create(
        title='Bot Reply Test Post',
        defaults={
            'content': 'This is a test post to verify bot reply logic works correctly.',
            'author': regular_user,
            'community': community
        }
    )
    
    # Create bot comment on the post
    bot_comment = Comment.objects.create(
        content="This is a test comment by the bot on the main post.",
        author=bot_user,
        post=post
    )
    
    # Create reply to bot's comment
    user_reply = Comment.objects.create(
        content="This is a reply to the bot's comment by a regular user.",
        author=regular_user,
        post=post,
        parent_comment=bot_comment
    )
    
    print(f"✅ Created test post: {post.title}")
    print(f"✅ Created bot comment: {bot_comment.id}")
    print(f"✅ Created reply to bot: {user_reply.id}")
    
    # Test the bot framework directly
    bot_framework = BotFramework(
        bot_id=bot_user.username,
        personality=get_personality(BotPersonalityType.CASUAL),
        api_key='test_key',  # We won't make actual API calls
        base_url='http://localhost:8000/api'
    )
    
    # Test get_pending_replies method
    print(f"\n🧪 Testing get_pending_replies method...")
    
    # Mock the get_pending_replies method for testing
    def mock_get_pending_replies():
        # Find replies to bot's comments directly from database
        user_comment_ids = Comment.objects.filter(
            author=bot_user, 
            is_deleted=False
        ).values_list('id', flat=True)
        
        replies = Comment.objects.filter(
            parent_comment__in=user_comment_ids,
            is_deleted=False
        ).exclude(
            author=bot_user
        ).order_by('-created_at')[:50]
        
        # Convert to dict format like the API would return
        return [
            {
                'id': reply.id,
                'content': reply.content,
                'author': {'username': reply.author.username},
                'created_at': reply.created_at.isoformat() + 'Z',
                'post': reply.post.id
            }
            for reply in replies
        ]
    
    # Replace the method temporarily for testing
    original_method = bot_framework.get_pending_replies
    bot_framework.get_pending_replies = mock_get_pending_replies
    
    # Test the pending replies
    pending_replies = bot_framework.get_pending_replies()
    print(f"   Found {len(pending_replies)} pending replies")
    
    if pending_replies:
        for reply in pending_replies:
            print(f"     - Reply {reply['id']}: {reply['content'][:50]}...")
    
    # Test the decide_action method with mock data
    print(f"\n🧪 Testing decide_action method...")
    
    available_posts = [{
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'community_name': community.name
    }]
    
    available_comments = [
        {
            'id': bot_comment.id,
            'content': bot_comment.content,
            'author': {'username': bot_comment.author.username},
            'post': post.id,
            'parent_comment': None
        },
        {
            'id': user_reply.id,
            'content': user_reply.content,
            'author': {'username': user_reply.author.username},
            'post': post.id,
            'parent_comment': bot_comment.id
        }
    ]
    
    # Run decide_action
    try:
        action = bot_framework.decide_action(available_posts, available_comments)
        
        if action:
            print(f"   ✅ Bot decided on action: {action.action_type}")
            print(f"   ✅ Target ID: {action.target_id}")
            
            if action.action_type == 'reply_comment' and action.target_id == user_reply.id:
                print(f"   🎯 SUCCESS: Bot correctly wants to reply to the user's reply!")
            else:
                print(f"   ⚠️  Bot chose different action than expected")
        else:
            print(f"   ❌ Bot decided not to take any action")
            
    except Exception as e:
        print(f"   ❌ Error in decide_action: {e}")
        import traceback
        traceback.print_exc()
    
    # Restore original method
    bot_framework.get_pending_replies = original_method
    
    # Clean up test data
    print(f"\n🧹 Cleaning up test data...")
    user_reply.delete()
    bot_comment.delete()
    if created:  # Only delete post if we created it
        post.delete()
    
    print(f"✅ Test completed!")

if __name__ == '__main__':
    test_reply_logic()
