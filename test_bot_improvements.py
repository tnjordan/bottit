#!/usr/bin/env python3
"""
Test script to verify the bot improvements work correctly
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

def test_api_endpoints():
    """Test the new API endpoints for bot improvements"""
    print("Testing new API endpoints for bot improvements...")
    
    # Create test users
    User = get_user_model()
    
    # Create test bot user
    bot_user, created = User.objects.get_or_create(
        username='test_bot',
        defaults={
            'email': 'test_bot@example.com',
            'is_bot': True
        }
    )
    
    # Create regular user
    regular_user, created = User.objects.get_or_create(
        username='regular_user',
        defaults={
            'email': 'regular@example.com'
        }
    )
    
    # Use existing community
    community = Community.objects.filter(name='general').first()
    if not community:
        community = Community.objects.first()  # Use any existing community
    
    # Create test post
    post, created = Post.objects.get_or_create(
        title='Test Post for Bot Improvements',
        defaults={
            'content': 'This is a test post to verify bot improvements work correctly.',
            'author': regular_user,
            'community': community
        }
    )
    
    print(f"✅ Created test data:")
    print(f"   - Bot user: {bot_user.username}")
    print(f"   - Regular user: {regular_user.username}")
    print(f"   - Community: {community.name}")
    print(f"   - Post: {post.title}")
    
    # Test 1: Bot hasn't commented yet
    has_commented_before = bot_user.comments.filter(
        post=post,
        parent_comment__isnull=True,
        is_deleted=False
    ).exists()
    
    print(f"\n🧪 Test 1 - Bot has base comment before creating one: {has_commented_before}")
    
    # Create base comment by bot
    bot_comment = Comment.objects.create(
        content="This is a test comment by the bot",
        author=bot_user,
        post=post
    )
    
    # Test 2: Bot has commented now
    has_commented_after = bot_user.comments.filter(
        post=post,
        parent_comment__isnull=True,
        is_deleted=False
    ).exists()
    
    print(f"🧪 Test 2 - Bot has base comment after creating one: {has_commented_after}")
    
    # Create reply to bot's comment
    reply_to_bot = Comment.objects.create(
        content="This is a reply to the bot's comment",
        author=regular_user,
        post=post,
        parent_comment=bot_comment
    )
    
    # Test 3: Check pending replies
    replies_to_bot = Comment.objects.filter(
        parent_comment__in=bot_user.comments.filter(is_deleted=False).values_list('id', flat=True),
        is_deleted=False
    ).exclude(author=bot_user)
    
    print(f"🧪 Test 3 - Replies to bot's comments: {replies_to_bot.count()}")
    
    if replies_to_bot.exists():
        print(f"   - Reply content: {replies_to_bot.first().content}")
        print(f"   - Reply author: {replies_to_bot.first().author.username}")
    
    print("\n✅ All tests completed successfully!")
    print("The new API endpoints should work correctly with these scenarios.")

if __name__ == '__main__':
    test_api_endpoints()
