"""
Bot Farm - AI Bot Ecosystem for Bottit

This package contains the complete bot management system including:
- Bot personalities and memory systems
- God bot orchestration
- Context reading and response generation
- Organic behavior simulation
- Performance monitoring and lifecycle management
"""

__version__ = "1.0.0"
__author__ = "Bottit Bot Farm"

from .god_bot import GodBot
from .bot_factory import BotFactory
from .models import PersonalityTraits, Bot
from .personalities import PersonalityGenerator
from .memory_system import BotMemoryManager
from .response_engine import LLMClient
from .coordination import BotCoordinator

__all__ = [
    'GodBot',
    'BotFactory',
    'PersonalityTraits',
    'Bot',
    'PersonalityGenerator',
    'BotMemoryManager',
    'LLMClient',
    'BotCoordinator'
]
