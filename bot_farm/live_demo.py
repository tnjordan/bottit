#!/usr/bin/env python3
"""
Bot Farm LIVE Demo - Actually makes API calls to create real content
"""

import sys
import os
from pathlib import Path
import time

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from bot_farm.personalities import BotPersonalityType, get_personality
from bot_farm.organizer import BotFarmOrganizer, BotConfig
from dotenv import load_dotenv

load_dotenv()


def create_live_bot_farm():
    """Create a bot farm that will make actual API calls"""
    print("🏭 CREATING LIVE BOT FARM")
    print("=" * 50)
    
    # Check if we have API URL
    api_url = os.getenv('BOTTIT_API_URL')
    if not api_url:
        print("❌ No BOTTIT_API_URL found in environment!")
        print("Please set your BOTTIT_API_URL in the .env file")
        return None
    
    # Load bot credentials
    import json
    from pathlib import Path
    
    credentials_file = Path(__file__).parent / "bot_credentials.json"
    if not credentials_file.exists():
        print("❌ No bot credentials found!")
        print("Run: .venv/bin/python bot_farm/create_bots.py --create")
        return None
    
    with open(credentials_file, 'r') as f:
        bot_credentials = json.load(f)
    
    print(f"🔗 API URL: {api_url}")
    print(f"🔑 Found {len(bot_credentials)} bot credentials")
    
    # Create organizer
    farm = BotFarmOrganizer(base_url=api_url)
    
    # Create a smaller but diverse set of bots for live testing
    live_bots = [
        # One of each personality type
        ("alice_enthusiast", BotPersonalityType.ENTHUSIAST),
        ("bob_critic", BotPersonalityType.CRITIC),
        ("charlie_helper", BotPersonalityType.HELPER),
        ("diana_lurker", BotPersonalityType.LURKER),
        ("eve_casual", BotPersonalityType.CASUAL),
        ("frank_intellectual", BotPersonalityType.INTELLECTUAL),
    ]
    
    print(f"\nAdding {len(live_bots)} bots to the farm:")
    
    for bot_id, personality_type in live_bots:
        if bot_id not in bot_credentials:
            print(f"❌ No credentials found for {bot_id}")
            continue
            
        bot_api_key = bot_credentials[bot_id]['api_key']
        
        config = BotConfig(
            bot_id=bot_id,
            personality_type=personality_type,
            api_key=bot_api_key  # Use the bot's individual API key
        )
        
        success = farm.add_bot(config)
        if success:
            bot = farm.bots[bot_id]
            print(f"  ✅ {bot_id}: {bot.personality.name} (activity: {bot.personality.activity_level})")
        else:
            print(f"  ❌ Failed to add {bot_id}")
    
    return farm


def run_live_cycles(farm, num_cycles=3, cycle_delay=10):
    """Run actual bot farm cycles with real API calls"""
    print(f"\n🚀 RUNNING {num_cycles} LIVE CYCLES")
    print("=" * 60)
    print(f"⏰ Delay between cycles: {cycle_delay} seconds")
    print("⚠️  This will make REAL API calls and create actual content!")
    
    # Ask for confirmation
    response = input("\nProceed with live API calls? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cancelled by user")
        return
    
    total_actions = 0
    
    for cycle in range(1, num_cycles + 1):
        print(f"\n{'='*20} CYCLE {cycle} {'='*20}")
        
        # Run one cycle
        results = farm.run_single_cycle()
        
        cycle_actions = len([r for r in results if "Executed" in r])
        total_actions += cycle_actions
        
        print(f"📊 Cycle {cycle} summary: {cycle_actions} successful actions")
        
        # Show individual results
        for result in results:
            if "Executed" in result:
                print(f"  ✅ {result}")
            elif "Failed" in result:
                print(f"  ❌ {result}")
            elif "No action" in result:
                print(f"  😴 {result}")
            else:
                print(f"  ℹ️  {result}")
        
        # Wait before next cycle (except for last cycle)
        if cycle < num_cycles:
            print(f"\n⏳ Waiting {cycle_delay} seconds before next cycle...")
            time.sleep(cycle_delay)
    
    print(f"\n🎉 LIVE DEMO COMPLETE!")
    print(f"📈 Total successful actions: {total_actions}")
    
    # Show final statistics
    stats = farm.get_farm_statistics()
    print(f"\n📊 Final Farm Statistics:")
    print(f"  Total bots: {stats['total_bots']}")
    print(f"  Total actions taken: {stats['total_actions']}")
    print(f"  Personality distribution: {stats['personality_distribution']}")
    
    # Show individual bot performance
    print(f"\n🤖 Individual Bot Performance:")
    for bot_id in farm.bots.keys():
        status = farm.get_bot_status(bot_id)
        print(f"  {bot_id}: {status['total_actions']} actions")


def test_api_connection():
    """Test if we can connect to the Bottit API"""
    print("🔍 TESTING API CONNECTION")
    print("=" * 40)
    
    import requests
    
    api_url = os.getenv('BOTTIT_API_URL')
    api_key = os.getenv('BOTTIT_ADMIN_API_KEY')
    
    if not api_url or not api_key:
        print("❌ Missing API_URL or API_KEY in environment")
        return False
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test getting posts
    try:
        print(f"🔗 Testing connection to: {api_url}")
        response = requests.get(f"{api_url}/posts/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            posts_data = response.json()
            post_count = len(posts_data.get('results', []))
            print(f"✅ API connection successful!")
            print(f"📋 Found {post_count} existing posts")
            return True
        else:
            print(f"❌ API returned status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False


def create_sample_post():
    """Create a single sample post to test the API"""
    print("\n📝 CREATING SAMPLE POST")
    print("=" * 30)
    
    import requests
    
    api_url = os.getenv('BOTTIT_API_URL')
    api_key = os.getenv('BOTTIT_ADMIN_API_KEY')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    sample_post = {
        'title': 'Bot Farm Test Post',
        'content': 'This is a test post created by the bot farm system to verify API connectivity.',
        'community_name': 'general'
    }
    
    try:
        response = requests.post(f"{api_url}/posts/", headers=headers, json=sample_post)
        
        if response.status_code == 201:
            post_data = response.json()
            print(f"✅ Sample post created successfully!")
            print(f"📋 Post ID: {post_data.get('id')}")
            print(f"📋 Title: {post_data.get('title')}")
            return post_data
        else:
            print(f"❌ Failed to create post: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating post: {e}")
        return None


def main():
    """Run the live bot farm demo"""
    print("🤖 BOT FARM LIVE DEMO")
    print("=" * 50)
    print("This demo makes REAL API calls to your Bottit instance!")
    
    import argparse
    parser = argparse.ArgumentParser(description='Bot Farm Live Demo')
    parser.add_argument('--test-connection', action='store_true', 
                       help='Test API connection only')
    parser.add_argument('--create-sample', action='store_true',
                       help='Create a sample post only')
    parser.add_argument('--cycles', type=int, default=3,
                       help='Number of cycles to run (default: 3)')
    parser.add_argument('--delay', type=int, default=10,
                       help='Seconds between cycles (default: 10)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would happen without making API calls')
    
    args = parser.parse_args()
    
    try:
        if args.test_connection:
            success = test_api_connection()
            if success:
                print("\n✅ API connection test successful!")
            else:
                print("\n❌ API connection test failed!")
            return
        
        if args.create_sample:
            result = create_sample_post()
            if result:
                print("\n✅ Sample post creation successful!")
            else:
                print("\n❌ Sample post creation failed!")
            return
        
        # Test connection first
        if not test_api_connection():
            print("\n❌ Cannot proceed - API connection failed")
            return
        
        # Create the farm
        farm = create_live_bot_farm()
        if not farm:
            print("\n❌ Failed to create bot farm")
            return
        
        if args.dry_run:
            print("\n🧪 DRY RUN MODE - No actual API calls will be made")
            # Run simulation like the original demo
            results = farm.run_single_cycle()
            print(f"Would have made {len(results)} actions")
        else:
            # Run live cycles
            run_live_cycles(farm, num_cycles=args.cycles, cycle_delay=args.delay)
        
        print("\n✅ Live demo completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
