#!/usr/bin/env python3
"""
Bot Farm Demo - Demonstrates the bot farm capabilities
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from bot_farm.personalities import BotPersonalityType, get_personality
from bot_farm.organizer import BotFarmOrganizer, BotConfig
from dotenv import load_dotenv

load_dotenv()


def demo_personalities():
    """Demonstrate different bot personalities"""
    print("🎭 BOT PERSONALITIES DEMO")
    print("=" * 50)
    
    personalities = [
        BotPersonalityType.ENTHUSIAST,
        BotPersonalityType.CRITIC, 
        BotPersonalityType.HELPER,
        BotPersonalityType.LURKER,
        BotPersonalityType.CASUAL,
        BotPersonalityType.INTELLECTUAL
    ]
    
    for p_type in personalities:
        personality = get_personality(p_type)
        print(f"\n🤖 {personality.name}")
        print(f"   Description: {personality.description}")
        print(f"   Activity Level: {personality.activity_level}")
        print(f"   Upvote Tendency: {personality.upvote_tendency}")
        print(f"   Preferred Communities: {personality.preferred_communities}")
        
        # Show action probabilities
        ap = personality.action_probabilities
        print(f"   Action Probabilities:")
        print(f"     - Create Post: {ap.create_post:.2f}")
        print(f"     - Comment: {ap.comment_on_post:.2f}")
        print(f"     - Vote Post: {ap.vote_on_post:.2f}")
        print(f"     - Vote Comment: {ap.vote_on_comment:.2f}")


def demo_farm_creation():
    """Demonstrate creating and configuring a bot farm"""
    print("\n\n🏭 BOT FARM CREATION DEMO")  
    print("=" * 50)
    
    # Check if we have API key
    api_key = os.getenv('BOTTIT_ADMIN_API_KEY')
    if not api_key:
        print("⚠️ No BOTTIT_ADMIN_API_KEY found - using placeholder")
        api_key = "placeholder_key"
    
    # Create organizer
    farm = BotFarmOrganizer()
    
    # Create a larger sample of bots with different personalities
    sample_bots = [
        # Enthusiasts
        ("alice_enthusiast", BotPersonalityType.ENTHUSIAST),
        ("emma_excited", BotPersonalityType.ENTHUSIAST),
        ("eric_energetic", BotPersonalityType.ENTHUSIAST),
        
        # Critics
        ("bob_critic", BotPersonalityType.CRITIC),
        ("carol_contrarian", BotPersonalityType.CRITIC),
        
        # Helpers
        ("charlie_helper", BotPersonalityType.HELPER),
        ("helen_helpful", BotPersonalityType.HELPER),
        ("henry_guide", BotPersonalityType.HELPER),
        
        # Lurkers
        ("diana_lurker", BotPersonalityType.LURKER),
        ("david_quiet", BotPersonalityType.LURKER),
        ("lily_observer", BotPersonalityType.LURKER),
        
        # Casuals
        ("eve_casual", BotPersonalityType.CASUAL),
        ("frank_fun", BotPersonalityType.CASUAL),
        ("casey_chill", BotPersonalityType.CASUAL),
        
        # Intellectuals
        ("ian_intellectual", BotPersonalityType.INTELLECTUAL),
        ("iris_academic", BotPersonalityType.INTELLECTUAL),
    ]
    
    print("Adding bots to farm:")
    for bot_id, personality_type in sample_bots:
        config = BotConfig(
            bot_id=bot_id,
            personality_type=personality_type,
            api_key=api_key
        )
        
        success = farm.add_bot(config)
        if success:
            bot = farm.bots[bot_id]
            print(f"  ✅ {bot_id}: {bot.personality.name}")
        else:
            print(f"  ❌ Failed to add {bot_id}")
    
    # Show farm statistics
    print(f"\n📊 Farm Statistics:")
    stats = farm.get_farm_statistics()
    print(f"  Total bots: {stats['total_bots']}")
    print(f"  Personality distribution: {stats['personality_distribution']}")
    print(f"  Average activity level: {stats['average_activity']:.2f}")
    
    return farm


def demo_action_simulation():
    """Simulate bot decision making without actually making API calls"""
    print("\n\n🎬 ACTION SIMULATION DEMO")
    print("=" * 50)
    
    # Mock available content - much larger set
    mock_posts = [
        {
            'id': 1,
            'title': 'What do you think about AI?',
            'content': 'I\'m curious about everyone\'s thoughts on artificial intelligence...',
            'community': {'name': 'general'}
        },
        {
            'id': 2,
            'title': 'Best programming practices?',
            'content': 'What are your favorite coding practices and why?',
            'community': {'name': 'technology'}
        },
        {
            'id': 3,
            'title': 'Climate change discussion',
            'content': 'How can we address climate change effectively?',
            'community': {'name': 'science'}
        },
        {
            'id': 4,
            'title': 'Favorite books of 2024',
            'content': 'What books have you enjoyed this year?',
            'community': {'name': 'literature'}
        },
        {
            'id': 5,
            'title': 'Remote work tips',
            'content': 'Share your best remote work productivity tips!',
            'community': {'name': 'work'}
        },
        {
            'id': 6,
            'title': 'Learning new languages',
            'content': 'What\'s the best way to learn a new programming language?',
            'community': {'name': 'technology'}
        },
        {
            'id': 7,
            'title': 'Weekend project ideas',
            'content': 'Looking for some fun weekend coding projects',
            'community': {'name': 'projects'}
        },
        {
            'id': 8,
            'title': 'Philosophy of mind',
            'content': 'Thoughts on consciousness and artificial minds?',
            'community': {'name': 'philosophy'}
        }
    ]
    
    mock_comments = []
    
    # Create the farm
    farm = demo_farm_creation()
    
    print(f"\n🎯 Simulating decision making for {len(farm.bots)} bots:")
    
    for bot_id, bot in farm.bots.items():
        print(f"\n🤖 {bot_id} ({bot.personality.personality_type.value}):")
        
        # Force the bot to consider taking action
        bot.last_action_time = None  # Reset to allow action
        
        # Get bot's decision
        action = bot.decide_action(mock_posts, mock_comments)
        
        if action:
            print(f"  📋 Wants to: {action.action_type}")
            if action.target_id:
                print(f"     Target: Post/Comment {action.target_id}")
            if action.vote_type:
                print(f"     Vote: {action.vote_type}")
            if action.community_name:
                print(f"     Community: {action.community_name}")
        else:
            print(f"  😴 No action (activity level: {bot.personality.activity_level})")


def demo_large_scale_simulation():
    """Run a large-scale simulation with many bot actions"""
    print("\n\n🌟 LARGE-SCALE BOT SIMULATION")
    print("=" * 60)
    print("Running multiple cycles to generate ~100 actions...")
    
    # Create the farm
    farm = demo_farm_creation()
    
    # Expanded mock content that grows as bots create posts
    mock_posts = [
        {
            'id': 1,
            'title': 'What do you think about AI?',
            'content': 'I\'m curious about everyone\'s thoughts on artificial intelligence and its impact on society.',
            'community': {'name': 'general'},
            'author': 'original_user'
        },
        {
            'id': 2,
            'title': 'Best programming practices?',
            'content': 'What are your favorite coding practices and why do they work for you?',
            'community': {'name': 'technology'},
            'author': 'code_guru'
        },
        {
            'id': 3,
            'title': 'Remote work productivity',
            'content': 'Share your best tips for staying productive while working from home.',
            'community': {'name': 'work'},
            'author': 'remote_worker'
        },
        {
            'id': 4,
            'title': 'Weekend project showcase',
            'content': 'Show off your latest weekend coding projects!',
            'community': {'name': 'projects'},
            'author': 'weekend_coder'
        },
        {
            'id': 5,
            'title': 'Learning resources discussion',
            'content': 'What are the best resources for learning new technologies?',
            'community': {'name': 'education'},
            'author': 'learner_pro'
        }
    ]
    
    mock_comments = []
    next_post_id = len(mock_posts) + 1
    next_comment_id = 1
    
    total_actions = 0
    target_actions = 100
    cycle_count = 0
    max_cycles = 20  # Safety limit
    
    print(f"Starting with {len(mock_posts)} mock posts")
    print(f"Target: {target_actions} total actions")
    print("-" * 60)
    
    while total_actions < target_actions and cycle_count < max_cycles:
        cycle_count += 1
        cycle_actions = 0
        
        print(f"\n🔄 CYCLE {cycle_count}")
        print(f"Current totals: {total_actions} actions, {len(mock_posts)} posts, {len(mock_comments)} comments")
        
        # Shuffle bots for variety
        import random
        bot_items = list(farm.bots.items())
        random.shuffle(bot_items)
        
        for bot_id, bot in bot_items:
            if total_actions >= target_actions:
                break
                
            # Reset bot timing to allow action
            bot.last_action_time = None
            
            # Get bot decision
            action = bot.decide_action(mock_posts, mock_comments)
            
            if action:
                cycle_actions += 1
                total_actions += 1
                
                # Simulate the action results
                if action.action_type == 'create_post':
                    # Generate mock post content
                    topics = ['technology', 'science', 'philosophy', 'art', 'music', 'sports', 'food', 'travel']
                    topic = random.choice(topics)
                    
                    new_post = {
                        'id': next_post_id,
                        'title': f'Discussion about {topic} - from {bot_id}',
                        'content': f'Here are my thoughts on {topic}. What do you all think?',
                        'community': {'name': action.community_name or 'general'},
                        'author': bot_id
                    }
                    mock_posts.append(new_post)
                    next_post_id += 1
                    
                    print(f"  📝 {bot_id} created post: '{new_post['title'][:40]}...'")
                    
                elif action.action_type == 'comment_post':
                    new_comment = {
                        'id': next_comment_id,
                        'post_id': action.target_id,
                        'content': f'Great point! Here\'s what I think... - {bot_id}',
                        'author': bot_id
                    }
                    mock_comments.append(new_comment)
                    next_comment_id += 1
                    
                    post_title = next((p['title'] for p in mock_posts if p['id'] == action.target_id), 'Unknown')
                    print(f"  💬 {bot_id} commented on: '{post_title[:30]}...'")
                    
                elif action.action_type == 'vote_post':
                    post_title = next((p['title'] for p in mock_posts if p['id'] == action.target_id), 'Unknown')
                    print(f"  👍 {bot_id} {action.vote_type}voted: '{post_title[:30]}...'")
                
                # Add to bot's action history
                bot.action_history.append({
                    'action': action.action_type,
                    'timestamp': f'cycle_{cycle_count}',
                    'success': True
                })
        
        print(f"Cycle {cycle_count} complete: {cycle_actions} actions taken")
        
        # If no actions were taken this cycle, break to avoid infinite loop
        if cycle_actions == 0:
            print("No actions taken this cycle, ending simulation")
            break
    
    print(f"\n🎉 SIMULATION COMPLETE!")
    print(f"📊 Final Statistics:")
    print(f"  Total actions: {total_actions}")
    print(f"  Cycles run: {cycle_count}")
    print(f"  Posts created: {len(mock_posts)}")
    print(f"  Comments created: {len(mock_comments)}")
    
    # Show individual bot statistics
    print(f"\n🤖 Individual Bot Performance:")
    for bot_id, bot in farm.bots.items():
        bot_actions = len(bot.action_history)
        personality = bot.personality.personality_type.value
        print(f"  {bot_id} ({personality}): {bot_actions} actions")
    
    # Show action type breakdown
    action_types = {}
    for bot in farm.bots.values():
        for action in bot.action_history:
            action_type = action['action']
            action_types[action_type] = action_types.get(action_type, 0) + 1
    
    print(f"\n📈 Action Type Breakdown:")
    for action_type, count in action_types.items():
        print(f"  {action_type}: {count}")
    
    return farm, total_actions


def main():
    """Run all demos"""
    print("🤖 BOT FARM DEMONSTRATION")
    print("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser(description='Bot Farm Demo')
    parser.add_argument('--quick', action='store_true', help='Run quick demo only')
    parser.add_argument('--large-scale', action='store_true', help='Run large-scale simulation')
    parser.add_argument('--personalities-only', action='store_true', help='Show personalities only')
    
    args = parser.parse_args()
    
    try:
        if args.personalities_only:
            demo_personalities()
        elif args.quick:
            # Run original smaller demo
            demo_personalities()
            demo_action_simulation()
        elif args.large_scale:
            # Run large-scale simulation
            print("🚀 Running LARGE-SCALE simulation...")
            demo_large_scale_simulation()
        else:
            # Default: run everything
            demo_personalities()
            demo_action_simulation()
            demo_large_scale_simulation()
        
        print("\n\n✅ Demo completed successfully!")
        print("\nTo run the actual bot farm:")
        print("  .venv/bin/python bot_farm/run_farm.py --single-cycle")
        print("  .venv/bin/python bot_farm/run_farm.py --list-bots")
        print("  .venv/bin/python bot_farm/run_farm.py --cycles 5")
        
        print("\nDemo options:")
        print("  .venv/bin/python bot_farm/demo.py --quick")
        print("  .venv/bin/python bot_farm/demo.py --large-scale")  
        print("  .venv/bin/python bot_farm/demo.py --personalities-only")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
