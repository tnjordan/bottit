"""
Bot Models and Data Structures

Core data models for the bot farm system
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid

from .config import BotRole, LLMProvider


class BotStatus(Enum):
    """Bot lifecycle status"""
    CREATING = "creating"
    ACTIVE = "active"
    INACTIVE = "inactive"
    OPTIMIZING = "optimizing"
    RETIRING = "retiring"
    RETIRED = "retired"


class InteractionType(Enum):
    """Types of bot interactions"""
    POST_CREATED = "post_created"
    COMMENT_CREATED = "comment_created"
    VOTE_CAST = "vote_cast"
    REPLY_SENT = "reply_sent"


@dataclass
class BotInteraction:
    """Record of a single bot interaction"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    bot_id: str = ""
    interaction_type: InteractionType = InteractionType.COMMENT_CREATED
    content_id: str = ""  # ID of post/comment interacted with
    community_name: str = ""
    content_text: str = ""
    response_text: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    context_used: Dict[str, Any] = field(default_factory=dict)
    quality_score: Optional[float] = None
    vote_score: int = 0
    replies_generated: int = 0
    success_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BotMemoryEntry:
    """Single memory entry for a bot"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    bot_id: str = ""
    topic: str = ""
    community: str = ""
    interaction_summary: str = ""
    learned_preferences: Dict[str, Any] = field(default_factory=dict)
    success_indicators: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    importance_score: float = 0.5  # 0-1, higher = more important to retain


@dataclass
class PersonalityTraits:
    """Bot personality configuration"""
    name: str = ""
    role: BotRole = BotRole.CONTENT_CREATOR
    communication_style: str = "casual and friendly"
    expertise_areas: List[str] = field(default_factory=list)
    response_length_preference: str = "medium"  # short, medium, long
    formality_level: str = "semi-formal"  # casual, semi-formal, formal
    emotional_tone: str = "helpful and positive"
    behavior_patterns: List[str] = field(default_factory=list)
    disagreement_style: str = "respectful with alternatives"
    curiosity_areas: List[str] = field(default_factory=list)
    avoidance_topics: List[str] = field(default_factory=list)
    interaction_guidelines: str = ""
    preferred_communities: List[str] = field(default_factory=list)
    activity_level: str = "moderate"  # low, moderate, high
    response_speed: str = "thoughtful"  # quick, thoughtful, slow


@dataclass
class BotPerformanceMetrics:
    """Bot performance tracking data"""
    bot_id: str = ""
    evaluation_period_start: datetime = field(default_factory=datetime.now)
    evaluation_period_end: datetime = field(default_factory=datetime.now)
    
    # Engagement metrics
    posts_created: int = 0
    comments_made: int = 0
    votes_cast: int = 0
    conversations_started: int = 0
    
    # Quality metrics
    average_post_score: float = 0.0
    average_comment_score: float = 0.0
    response_quality_avg: float = 0.0
    consistency_score: float = 0.0
    
    # Community integration
    communities_active_in: List[str] = field(default_factory=list)
    community_acceptance_scores: Dict[str, float] = field(default_factory=dict)
    
    # Learning indicators
    improvement_trend: float = 0.0  # Positive = improving
    adaptation_score: float = 0.0
    
    # Overall scores
    overall_performance_score: float = 0.0
    recommendation: str = "continue"  # continue, optimize, retire


@dataclass
class Bot:
    """Main bot data structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    user_id: int = 0  # Django user ID
    api_key: str = ""
    
    # Personality and behavior
    personality: PersonalityTraits = field(default_factory=PersonalityTraits)
    memory_entries: List[BotMemoryEntry] = field(default_factory=list)
    interaction_history: List[BotInteraction] = field(default_factory=list)
    
    # Status and metadata
    status: BotStatus = BotStatus.CREATING
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    created_by_god_bot: bool = True
    creation_reason: str = ""
    
    # Assignment and configuration
    assigned_communities: List[str] = field(default_factory=list)
    llm_provider: LLMProvider = LLMProvider.GOOGLE
    
    # Performance tracking
    latest_performance: Optional[BotPerformanceMetrics] = None
    performance_history: List[BotPerformanceMetrics] = field(default_factory=list)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get bot summary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'role': self.personality.role.value,
            'status': self.status.value,
            'communities': self.assigned_communities,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'performance_score': self.latest_performance.overall_performance_score if self.latest_performance else 0.0
        }


@dataclass
class EcosystemHealth:
    """Overall bot ecosystem health metrics"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Bot population
    total_bots: int = 0
    active_bots: int = 0
    bots_created_today: int = 0
    bots_retired_today: int = 0
    
    # Community coverage
    communities_with_bots: int = 0
    avg_bots_per_community: float = 0.0
    underserved_communities: List[str] = field(default_factory=list)
    
    # Activity metrics
    total_bot_posts_24h: int = 0
    total_bot_comments_24h: int = 0
    avg_bot_performance: float = 0.0
    
    # Quality indicators
    avg_content_quality: float = 0.0
    bot_detection_rate: float = 0.0  # Lower is better
    user_satisfaction_proxy: float = 0.0
    
    # System health
    overall_health_score: float = 0.0  # 0-1, higher is better
    recommendations: List[str] = field(default_factory=list)


@dataclass
class PlatformAnalysis:
    """Analysis of platform needs and opportunities"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Community analysis
    community_activity_scores: Dict[str, float] = field(default_factory=dict)
    inactive_communities: List[str] = field(default_factory=list)
    growing_communities: List[str] = field(default_factory=list)
    
    # Content analysis
    content_gaps: List[Dict[str, Any]] = field(default_factory=list)
    trending_topics: List[str] = field(default_factory=list)
    underserved_topics: List[str] = field(default_factory=list)
    
    # User engagement
    avg_discussion_depth: float = 0.0
    communities_needing_facilitation: List[str] = field(default_factory=list)
    
    # Bot creation recommendations
    recommended_bots: List[Dict[str, Any]] = field(default_factory=list)
