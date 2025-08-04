"""
Bot Farm Configuration
"""

import os
import django
import random
from typing import Dict, Any, List, Optional
from .personalities import BotPersonalityType, get_personality

def get_dynamic_bot_configs() -> Dict[str, Any]:
    """
    Dynamically discover all bot users from the database and assign personalities
    """
    # Configuration - modify these values as needed
    DESIRED_BOT_COUNT = 25  # How many bots to run (will use max available if more than actual bots)
    
    # Personality selection - set to None to use all personalities, or specify a list
    ALLOWED_PERSONALITIES: Optional[List[BotPersonalityType]] = None
    # Example: ALLOWED_PERSONALITIES = [BotPersonalityType.INCEL, BotPersonalityType.KAREN, BotPersonalityType.TROLL]
    
    # Set up Django if not already done
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bottit.settings')
    try:
        django.setup()
    except RuntimeError:
        pass  # Django already configured
    
    from core.models import CustomUser
    
    # Get all bot users
    all_bots = CustomUser.objects.filter(is_bot=True)
    
    # Determine how many bots to actually use
    actual_bot_count = min(DESIRED_BOT_COUNT, len(all_bots))
    
    # Randomly select the bots to use
    selected_bots = random.sample(list(all_bots), actual_bot_count)
    
    # Determine which personalities to use
    if ALLOWED_PERSONALITIES is None:
        # Use all available personalities
        available_personalities = list(BotPersonalityType)
    else:
        # Use only the specified personalities
        available_personalities = ALLOWED_PERSONALITIES
    
    bot_configs = {}
    
    for bot in selected_bots:
        # Randomly assign a personality type
        personality_type = random.choice(available_personalities)
        personality = get_personality(personality_type)
        
        # Create config for this bot
        config = {
            "personality_type": personality_type.value,
            "api_key": bot.api_key,  # Use the bot's actual API key
            "custom_overrides": {
                "activity_level": personality.activity_level,
                "preferred_communities": personality.preferred_communities.copy(),
                "upvote_tendency": personality.upvote_tendency,
                "downvote_tendency": personality.downvote_tendency
            }
        }
        
        bot_configs[bot.username] = config
    
    print(f"Configured {len(bot_configs)} bots with random personalities from {len(available_personalities)} available types")
    
    return bot_configs

# Get the dynamic bot configurations
BOT_CONFIGS = get_dynamic_bot_configs()

# Farm operation settings - Optimized for focused engagement
FARM_SETTINGS = {
    "cycle_interval": 2,  # Much shorter intervals for active conversation (was 60)
    "max_concurrent_bots": 17,  # Fewer concurrent bots for more focused interaction (was 5)
    "content_fetch_limit": 50,  # Get more comments for complete conversation context (was 20)
    "enable_logging": True,
    "log_file": "bot_farm.log",
    "focus_mode": True,  # New: Only work on latest post
    "conversation_depth": True  # New: Prioritize replies over new posts
}

# Safety settings - Adjusted for focused engagement
SAFETY_SETTINGS = {
    "max_posts_per_bot_per_hour": 100_000,  # Very limited post creation (was 2)
    "max_comments_per_bot_per_hour": 100_000,  # Allow more comments for active conversation (was 10)
    "min_action_interval": 10,  # Shorter interval for more active engagement (was 30)
    "enable_rate_limiting": True,
    "max_base_comments_per_post": 1,  # New: Strict rule - only one base comment per bot per post
    "prioritize_replies": True  # New: Heavily favor replies over new base comments
}
