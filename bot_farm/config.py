"""
Bot Farm Configuration
"""

import os
import django
from typing import Dict, Any
from .personalities import BotPersonalityType, get_personality

def get_dynamic_bot_configs() -> Dict[str, Any]:
    """
    Dynamically discover all bot users from the database and assign personalities
    """
    # Set up Django if not already done
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bottit.settings')
    try:
        django.setup()
    except RuntimeError:
        pass  # Django already configured
    
    from core.models import CustomUser
    
    # Get all bot users
    bots = CustomUser.objects.filter(is_bot=True)
    
    # Use only INCEL personality type
    personality_type = BotPersonalityType.INCEL.value
    
    # Get the INCEL personality configuration
    incel_personality = get_personality(BotPersonalityType.INCEL)
    
    bot_configs = {}
    
    for bot in bots:
        # Create config for this bot using INCEL personality
        config = {
            "personality_type": personality_type,
            "api_key": bot.api_key,  # Use the bot's actual API key
            "custom_overrides": {
                "activity_level": incel_personality.activity_level,
                "preferred_communities": incel_personality.preferred_communities.copy(),
                "upvote_tendency": incel_personality.upvote_tendency,
                "downvote_tendency": incel_personality.downvote_tendency
            }
        }
        
        bot_configs[bot.username] = config
    
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
