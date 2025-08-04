#!/usr/bin/env python3
"""
Bot Farm Organizer - Master program that manages multiple bots
"""

import os
import time
import random
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import google.generativeai as genai
from dotenv import load_dotenv

from .personalities import BotPersonality, BotPersonalityType, get_personality, get_random_personality
from .bot_framework import BotFramework, BotAction

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Bottit API config
BOTTIT_API_URL = os.getenv('BOTTIT_API_URL')
BOTTIT_API_KEY = os.getenv('BOTTIT_ADMIN_API_KEY')


@dataclass
class BotConfig:
    """Configuration for a single bot"""
    bot_id: str
    personality_type: BotPersonalityType
    api_key: str
    custom_overrides: Dict = None


class BotFarmOrganizer:
    """Master organizer that manages multiple bots with different personalities"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or BOTTIT_API_URL
        self.bots: Dict[str, BotFramework] = {}
        self.admin_api_key = BOTTIT_API_KEY
        self.running = False
        
    def add_bot(self, config: BotConfig) -> bool:
        """Add a new bot to the farm"""
        try:
            # Get personality template
            if config.custom_overrides:
                from .personalities import create_custom_personality
                personality = create_custom_personality(
                    config.personality_type, 
                    config.custom_overrides
                )
            else:
                personality = get_personality(config.personality_type)
            
            # Create bot framework instance
            bot = BotFramework(
                bot_id=config.bot_id,
                personality=personality,
                api_key=config.api_key,
                base_url=self.base_url
            )
            
            self.bots[config.bot_id] = bot
            print(f"✅ Added bot: {config.bot_id} ({personality.personality_type.value})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add bot {config.bot_id}: {e}")
            return False
    
    def remove_bot(self, bot_id: str) -> bool:
        """Remove a bot from the farm"""
        if bot_id in self.bots:
            del self.bots[bot_id]
            print(f"✅ Removed bot: {bot_id}")
            return True
        return False
    
    def get_bot_status(self, bot_id: str = None) -> Dict:
        """Get status of specific bot or all bots"""
        if bot_id:
            if bot_id in self.bots:
                bot = self.bots[bot_id]
                return {
                    'bot_id': bot_id,
                    'personality': bot.personality.personality_type.value,
                    'last_action': bot.last_action_time,
                    'total_actions': len(bot.action_history),
                    'activity_level': bot.personality.activity_level
                }
            return {}
        
        # Return status for all bots
        return {
            bot_id: {
                'personality': bot.personality.personality_type.value,
                'last_action': bot.last_action_time,
                'total_actions': len(bot.action_history),
                'activity_level': bot.personality.activity_level
            }
            for bot_id, bot in self.bots.items()
        }
    
    def fetch_available_content(self) -> Tuple[List[Dict], List[Dict]]:
        """Fetch only the most recent post and its comments for focused bot interaction"""
        try:
            headers = {
                'Authorization': f'Bearer {self.admin_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Get only the most recent post - bots will focus exclusively on this
            posts_response = requests.get(f"{self.base_url}/posts/", headers=headers)
            posts = []
            latest_post_id = None
            
            if posts_response.status_code == 200:
                posts_data = posts_response.json()
                all_posts = posts_data.get('results', [])
                if all_posts:
                    # Take only the most recent post - this ensures all bot activity is concentrated
                    latest_post = all_posts[0]
                    posts = [latest_post]  # Single post array to maintain API compatibility
                    latest_post_id = latest_post['id']
                    print(f"🎯 Bots will focus on latest post: '{latest_post.get('title', 'Unknown')}' (ID: {latest_post_id})")
            
            # Get comments only for the latest post - bots only interact with current discussion
            comments = []
            if latest_post_id:
                # Use query parameter to filter comments by post ID
                comments_url = f"{self.base_url}/comments/?post={latest_post_id}"
                print(f"🔍 Fetching comments from: {comments_url}")
                comments_response = requests.get(comments_url, headers=headers)
                if comments_response.status_code == 200:
                    comments_data = comments_response.json()
                    all_comments = comments_data.get('results', [])
                    print(f"📊 API returned {len(all_comments)} comments for post {latest_post_id}")
                    
                    comments = all_comments[:10]  # Limit to 10 most recent comments for focused interaction
                else:
                    print(f"❌ Failed to fetch comments: {comments_response.status_code}")
            
            return posts, comments
            
        except Exception as e:
            print(f"❌ Error fetching content: {e}")
            return [], []
    
    def run_bot_cycle(self, bot_id: str, available_posts: List[Dict], available_comments: List[Dict]) -> Optional[str]:
        """Run one decision/action cycle for a specific bot"""
        if bot_id not in self.bots:
            return None
            
        bot = self.bots[bot_id]
        
        try:
            print(f"🤖 {bot_id} evaluating actions with {len(available_posts)} posts and {len(available_comments)} comments")
            
            # Bot decides what action to take
            action = bot.decide_action(
                available_posts,
                available_comments
            )
            
            if action is None:
                return f"{bot_id}: No action taken (cooldown or no valid actions)"
            
            print(f"🎬 {bot_id} executing {action.action_type} on target {action.target_id}")
            
            # Execute the action
            success = bot.execute_action(action)
            
            if success:
                return f"{bot_id}: ✅ Executed {action.action_type}"
            else:
                return f"{bot_id}: ❌ Failed to execute {action.action_type}"
                
        except Exception as e:
            print(f"❌ Exception in bot cycle for {bot_id}: {e}")
            return f"{bot_id}: Error - {e}"
    
    def run_single_cycle(self) -> List[str]:
        """Run one decision/action cycle for all bots - focused on the most recent post only"""
        print(f"\n🔄 Running bot cycle at {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        # Fetch current state of the platform - only the most recent post and its comments
        available_posts, available_comments = self.fetch_available_content()
        if available_posts:
            latest_post = available_posts[0]
            print(f"🎯 ALL BOTS focusing on latest post: '{latest_post.get('title', 'Unknown')}' with {len(available_comments)} comments")
            print(f"📍 Post ID: {latest_post['id']} | Community: {latest_post.get('community_name', 'Unknown')}")
        else:
            print("📋 No recent posts found - bots will create new content")
        
        results = []
        
        # Run bots in parallel for efficiency
        with ThreadPoolExecutor(max_workers=min(len(self.bots), 5)) as executor:
            future_to_bot = {
                executor.submit(self.run_bot_cycle, bot_id, available_posts, available_comments): bot_id
                for bot_id in self.bots.keys()
            }
            
            for future in as_completed(future_to_bot):
                bot_id = future_to_bot[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        print(f"  {result}")
                except Exception as e:
                    error_msg = f"{bot_id}: Exception - {e}"
                    results.append(error_msg)
                    print(f"  {error_msg}")
        
        print("-" * 60)
        return results
    
    def run_continuous(self, cycle_interval: int = 30, max_cycles: int = None):
        """Run the bot farm continuously"""
        print(f"🚀 Starting Bot Farm with {len(self.bots)} bots")
        print(f"⏰ Cycle interval: {cycle_interval} seconds")
        if max_cycles:
            print(f"🔢 Max cycles: {max_cycles}")
        print("=" * 60)
        
        self.running = True
        cycle_count = 0
        
        try:
            while self.running:
                cycle_count += 1
                
                print(f"\n🌟 CYCLE {cycle_count}")
                self.run_single_cycle()
                
                if max_cycles and cycle_count >= max_cycles:
                    print(f"\n✅ Completed {max_cycles} cycles")
                    break
                
                if self.running:
                    print(f"😴 Sleeping for {cycle_interval} seconds...")
                    time.sleep(cycle_interval)
                
        except KeyboardInterrupt:
            print("\n⏹️ Stopping bot farm...")
            self.running = False
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
        
        print("🏁 Bot farm stopped")
    
    def stop(self):
        """Stop the bot farm"""
        self.running = False
    
    def get_farm_statistics(self) -> Dict:
        """Get overall statistics for the bot farm"""
        total_actions = sum(len(bot.action_history) for bot in self.bots.values())
        
        personality_counts = {}
        for bot in self.bots.values():
            p_type = bot.personality.personality_type.value
            personality_counts[p_type] = personality_counts.get(p_type, 0) + 1
        
        return {
            'total_bots': len(self.bots),
            'total_actions': total_actions,
            'personality_distribution': personality_counts,
            'average_activity': sum(bot.personality.activity_level for bot in self.bots.values()) / len(self.bots) if self.bots else 0
        }


def create_sample_bot_farm() -> BotFarmOrganizer:
    """Create a sample bot farm with different personalities"""
    organizer = BotFarmOrganizer()
    
    # Define sample bots with different personalities
    sample_bots = [
        BotConfig(
            bot_id="enthusiast_alice",
            personality_type=BotPersonalityType.ENTHUSIAST,
            api_key=BOTTIT_API_KEY,  # In real scenario, each bot would have its own key
        ),
        BotConfig(
            bot_id="critic_bob",
            personality_type=BotPersonalityType.CRITIC,
            api_key=BOTTIT_API_KEY,
        ),
        BotConfig(
            bot_id="helper_charlie",
            personality_type=BotPersonalityType.HELPER,
            api_key=BOTTIT_API_KEY,
        ),
        BotConfig(
            bot_id="lurker_diana",
            personality_type=BotPersonalityType.LURKER,
            api_key=BOTTIT_API_KEY,
        ),
        BotConfig(
            bot_id="casual_eve",
            personality_type=BotPersonalityType.CASUAL,
            api_key=BOTTIT_API_KEY,
        )
    ]
    
    # Add bots to the farm
    for bot_config in sample_bots:
        organizer.add_bot(bot_config)
    
    return organizer


def main():
    """Main function to run the bot farm"""
    print("🤖 Bot Farm Organizer")
    print("=" * 40)
    
    # Create sample bot farm
    farm = create_sample_bot_farm()
    
    # Display farm info
    print(f"Created farm with {len(farm.bots)} bots:")
    for bot_id, bot in farm.bots.items():
        print(f"  - {bot_id}: {bot.personality.personality_type.value}")
    
    print("\nFarm Statistics:")
    stats = farm.get_farm_statistics()
    print(f"  Total bots: {stats['total_bots']}")
    print(f"  Personality distribution: {stats['personality_distribution']}")
    print(f"  Average activity level: {stats['average_activity']:.2f}")
    
    # Run a few cycles
    print("\n" + "=" * 60)
    print("🎬 Starting bot farm operation...")
    
    try:
        farm.run_continuous(cycle_interval=45, max_cycles=5)  # Run 5 cycles with 45s intervals
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
    
    # Final statistics
    print("\n📊 Final Statistics:")
    final_stats = farm.get_farm_statistics()
    print(f"  Total actions taken: {final_stats['total_actions']}")
    
    # Individual bot statistics
    print("\n🤖 Individual Bot Statistics:")
    for bot_id in farm.bots.keys():
        status = farm.get_bot_status(bot_id)
        print(f"  {bot_id}: {status['total_actions']} actions, last active: {status['last_action']}")


if __name__ == "__main__":
    main()
