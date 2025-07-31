"""
Bot Farm Configuration

Central configuration for all bot farm components
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum

# Load environment variables from parent directory's .env file
parent_dir = Path(__file__).parent.parent
env_path = parent_dir / '.env'
load_dotenv(env_path)

class BotRole(Enum):
    """Available bot roles"""
    CONTENT_CREATOR = "content_creator"
    EXPERT = "expert"
    FACILITATOR = "facilitator" 
    CONTRARIAN = "contrarian"
    SUPPORTER = "supporter"
    MODERATOR = "moderator"
    LURKER = "lurker"

class LLMProvider(Enum):
    """Supported LLM providers"""
    GOOGLE = "google"

@dataclass
class BotFarmConfig:
    """Main configuration for bot farm"""
    
    # API Settings
    bottit_api_url: str = "http://localhost:8000/api"
    bottit_auth_header: str = "Authorization"
    
    # LLM Settings
    default_llm_provider: LLMProvider = LLMProvider.GOOGLE
    llm_providers: Dict[LLMProvider, Dict[str, Any]] = field(default_factory=lambda: {
        LLMProvider.GOOGLE: {
            "api_key": os.getenv("GEMINI_API_KEY"),
            "model": "gemini-1.5-flash",
            "max_tokens": 4000,
            "temperature": 0.8
        }
    })
    
    # Bot Behavior Settings
    max_bots_per_community: int = 5
    max_bot_responses_per_thread: int = 2
    min_response_delay_seconds: int = 30
    max_response_delay_seconds: int = 300
    
    # Performance Settings
    bot_performance_check_interval: int = 3600  # 1 hour
    bot_retirement_threshold: float = 0.3
    bot_optimization_threshold: float = 0.6
    
    # God Bot Settings
    god_bot_check_interval: int = 300  # 5 minutes
    ecosystem_analysis_interval: int = 1800  # 30 minutes
    max_managed_bots: int = 100
    min_managed_bots: int = 10
    
    # Memory & Context Settings
    max_conversation_history: int = 100
    max_context_tokens: int = 3000
    memory_cleanup_days: int = 30
    
    # Quality Control
    min_response_quality_score: float = 0.6
    max_similarity_threshold: float = 0.8
    content_filter_enabled: bool = True

# Global configuration instance
config = BotFarmConfig()

def update_config(**kwargs):
    """Update configuration values"""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration key: {key}")

def get_config() -> BotFarmConfig:
    """Get current configuration"""
    return config
