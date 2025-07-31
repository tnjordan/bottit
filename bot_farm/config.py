"""
Bot Farm Configuration
"""

# Bot personalities and configurations
BOT_CONFIGS = {
    "enthusiast_alice": {
        "personality_type": "enthusiast",
        "custom_overrides": {
            "activity_level": 0.9,  # Very active
            "preferred_communities": ["general", "technology", "innovation"]
        }
    },
    "critic_bob": {
        "personality_type": "critic",
        "custom_overrides": {
            "activity_level": 0.6,  # Moderate activity
            "preferred_communities": ["general", "debate"]
        }
    },
    "helper_charlie": {
        "personality_type": "helper",
        "custom_overrides": {
            "activity_level": 0.8,  # High activity for helping
            "preferred_communities": ["general", "help", "questions"]
        }
    },
    "lurker_diana": {
        "personality_type": "lurker",
        "custom_overrides": {
            "activity_level": 1.0,  # Always active but mostly voting
            "upvote_tendency": 0.8,  # Likes to upvote
        }
    },
    "casual_eve": {
        "personality_type": "casual",
        "custom_overrides": {
            "activity_level": 0.7,
            "preferred_communities": ["general", "casual", "random"]
        }
    },
    "intellectual_frank": {
        "personality_type": "intellectual",
        "custom_overrides": {
            "activity_level": 0.4,  # Less frequent but more thoughtful
            "preferred_communities": ["general", "science", "philosophy"]
        }
    }
}

# Farm operation settings
FARM_SETTINGS = {
    "cycle_interval": 60,  # seconds between cycles
    "max_concurrent_bots": 5,  # max bots running simultaneously
    "content_fetch_limit": 20,  # max posts/comments to fetch
    "enable_logging": True,
    "log_file": "bot_farm.log"
}

# Safety settings
SAFETY_SETTINGS = {
    "max_posts_per_bot_per_hour": 2,  # Prevent spam
    "max_comments_per_bot_per_hour": 10,
    "min_action_interval": 30,  # seconds between actions for same bot
    "enable_rate_limiting": True
}
