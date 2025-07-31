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
from .personalities import BotPersonality
from .memory_system import BotMemory
from .response_engine import ResponseEngine
from .coordination import BotCoordinator

__all__ = [
    'GodBot',
    'BotFactory', 
    'BotPersonality',
    'BotMemory',
    'ResponseEngine',
    'BotCoordinator'
]
