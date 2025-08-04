"""
Bot Farm Configuration
"""

import os
import django
from typing import Dict, Any

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
    
    # Personality types to cycle through
    personality_types = ["enthusiast", "critic", "helper", "lurker", "casual", "intellectual"]
    
    # Community options for different personalities
    community_preferences = {
        "enthusiast": ["general", "technology", "innovation"],
        "critic": ["general", "debate"],
        "helper": ["general", "help", "questions"],
        "lurker": ["general"],  # Lurkers don't post much, so fewer communities
        "casual": ["general", "casual", "random"],
        "intellectual": ["general", "science", "philosophy"]
    }
    
    # Activity levels for different personalities
    activity_levels = {
        "enthusiast": 0.9,
        "critic": 0.6,
        "helper": 0.8,
        "lurker": 1.0,  # High activity but mostly voting
        "casual": 0.7,
        "intellectual": 0.4
    }
    
    bot_configs = {}
    
    for i, bot in enumerate(bots):
        # Cycle through personality types
        personality_type = personality_types[i % len(personality_types)]
        
        # Create config for this bot
        config = {
            "personality_type": personality_type,
            "api_key": bot.api_key,  # Use the bot's actual API key
            "custom_overrides": {
                "activity_level": activity_levels[personality_type],
                "preferred_communities": community_preferences[personality_type].copy()
            }
        }
        
        # Special handling for lurkers
        if personality_type == "lurker":
            config["custom_overrides"]["upvote_tendency"] = 0.8
        
        bot_configs[bot.username] = config
    
    return bot_configs

# Get the dynamic bot configurations
BOT_CONFIGS = get_dynamic_bot_configs()

# Farm operation settings - Optimized for focused engagement
FARM_SETTINGS = {
    "cycle_interval": 15,  # Much shorter intervals for active conversation (was 60)
    "max_concurrent_bots": 3,  # Fewer concurrent bots for more focused interaction (was 5)
    "content_fetch_limit": 50,  # Get more comments for complete conversation context (was 20)
    "enable_logging": True,
    "log_file": "bot_farm.log",
    "focus_mode": True,  # New: Only work on latest post
    "conversation_depth": True  # New: Prioritize replies over new posts
}

# Safety settings - Adjusted for focused engagement
SAFETY_SETTINGS = {
    "max_posts_per_bot_per_hour": 1,  # Very limited post creation (was 2)
    "max_comments_per_bot_per_hour": 20,  # Allow more comments for active conversation (was 10)
    "min_action_interval": 10,  # Shorter interval for more active engagement (was 30)
    "enable_rate_limiting": True,
    "max_base_comments_per_post": 1,  # New: Strict rule - only one base comment per bot per post
    "prioritize_replies": True  # New: Heavily favor replies over new base comments
}
