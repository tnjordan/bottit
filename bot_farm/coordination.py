"""
Bot Coordination System

Manages bot interactions, prevents artificial patterns, and ensures organic behavior
"""

import asyncio
import random
import time
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .models import Bot, BotStatus, InteractionType, BotInteraction
from .config import get_config


class ActivityType(Enum):
    """Types of bot activities"""
    READ_CONTENT = "read_content"
    CREATE_POST = "create_post"
    CREATE_COMMENT = "create_comment"
    CAST_VOTE = "cast_vote"
    BROWSE_COMMUNITY = "browse_community"


@dataclass
class BotActivity:
    """Represents a scheduled bot activity"""
    id: str
    bot_id: str
    activity_type: ActivityType
    target_content_id: Optional[str] = None
    community_name: Optional[str] = None
    scheduled_time: datetime = field(default_factory=datetime.now)
    priority: int = 5  # 1-10, higher = more urgent
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommunityActivityState:
    """Tracks recent activity in a community"""
    community_name: str
    recent_bot_posts: List[str] = field(default_factory=list)  # Bot IDs
    recent_bot_comments: List[str] = field(default_factory=list)  # Bot IDs
    last_bot_activity: Optional[datetime] = None
    human_activity_level: str = "unknown"  # low, medium, high


class OrganicTimingEngine:
    """Generates realistic delays and timing patterns for bot activities"""
    
    def __init__(self):
        self.config = get_config()
    
    def calculate_reading_delay(self, content_length: int, bot_personality: str = "normal") -> int:
        """Calculate how long a bot should 'read' content before responding"""
        
        # Base reading speed (words per minute)
        base_wpm = {
            "quick": 300,
            "normal": 200,
            "thoughtful": 150,
            "slow": 100
        }.get(bot_personality, 200)
        
        # Estimate word count (rough)
        estimated_words = content_length // 5
        
        # Calculate base reading time in seconds
        base_time = (estimated_words / base_wpm) * 60
        
        # Add human-like variation (±30%)
        variation = random.uniform(-0.3, 0.3)
        actual_time = base_time * (1 + variation)
        
        # Add minimum and maximum bounds
        min_time = self.config.min_response_delay_seconds
        max_time = self.config.max_response_delay_seconds
        
        return max(min_time, min(max_time, int(actual_time)))
    
    def calculate_typing_delay(self, response_length: int, bot_personality: str = "normal") -> int:
        """Calculate typing delay based on response length"""
        
        # Typing speed (words per minute)
        typing_wpm = {
            "quick": 80,
            "normal": 60,
            "thoughtful": 40,
            "slow": 30
        }.get(bot_personality, 60)
        
        words = response_length // 5
        typing_time = (words / typing_wpm) * 60
        
        # Add thinking pauses for longer responses
        if words > 50:
            thinking_pauses = random.randint(1, 3) * random.randint(10, 30)
            typing_time += thinking_pauses
        
        # Add variation
        variation = random.uniform(-0.2, 0.2)
        actual_time = typing_time * (1 + variation)
        
        return max(5, int(actual_time))  # Minimum 5 seconds
    
    def should_bot_be_active(self, bot: Bot, current_time: datetime) -> bool:
        """Determine if bot should be active based on realistic patterns"""
        
        # Check if bot is in active status
        if bot.status != BotStatus.ACTIVE:
            return False
        
        # Activity level affects probability
        activity_probabilities = {
            "low": 0.1,      # 10% chance per check
            "moderate": 0.3,  # 30% chance per check
            "high": 0.6       # 60% chance per check
        }
        
        base_probability = activity_probabilities.get(bot.personality.activity_level, 0.3)
        
        # Adjust based on time since last activity
        time_since_active = current_time - bot.last_active
        hours_inactive = time_since_active.total_seconds() / 3600
        
        # Increase probability if bot has been inactive for a while
        if hours_inactive > 4:
            base_probability *= 1.5
        elif hours_inactive > 8:
            base_probability *= 2.0
        
        # Decrease probability if bot was very recently active
        if hours_inactive < 0.5:
            base_probability *= 0.3
        
        return random.random() < base_probability


class BotCoordinator:
    """Coordinates bot activities to ensure organic patterns"""
    
    def __init__(self):
        self.config = get_config()
        self.timing_engine = OrganicTimingEngine()
        self.activity_queue: List[BotActivity] = []
        self.community_states: Dict[str, CommunityActivityState] = {}
        self.active_bots: Set[str] = set()
        self.recent_interactions: Dict[str, List[datetime]] = {}  # content_id -> timestamps
    
    async def coordinate_bot_activity(self, bots: List[Bot], 
                                     platform_events: List[Dict[str, Any]]) -> List[BotActivity]:
        """Main coordination method - decides what bots should do"""
        
        scheduled_activities = []
        current_time = datetime.now()
        
        # Update community states
        await self._update_community_states(platform_events)
        
        # Process each platform event
        for event in platform_events:
            activities = await self._process_platform_event(event, bots, current_time)
            scheduled_activities.extend(activities)
        
        # Schedule organic content creation
        creation_activities = await self._schedule_content_creation(bots, current_time)
        scheduled_activities.extend(creation_activities)
        
        # Apply coordination filters
        filtered_activities = self._apply_coordination_filters(scheduled_activities)
        
        return filtered_activities
    
    async def _process_platform_event(self, event: Dict[str, Any], 
                                     bots: List[Bot], current_time: datetime) -> List[BotActivity]:
        """Process a single platform event and determine bot responses"""
        
        activities = []
        event_type = event.get('type')
        content_id = event.get('content_id')
        community = event.get('community')
        
        # Find interested bots
        interested_bots = self._find_interested_bots(event, bots)
        
        # Apply selection filters
        selected_bots = self._select_bots_for_event(interested_bots, event, current_time)
        
        # Schedule activities for selected bots
        for bot in selected_bots:
            if event_type == 'new_post':
                activity = await self._schedule_post_response(bot, event, current_time)
            elif event_type == 'new_comment':
                activity = await self._schedule_comment_response(bot, event, current_time)
            elif event_type == 'trending_discussion':
                activity = await self._schedule_discussion_participation(bot, event, current_time)
            else:
                continue
            
            if activity:
                activities.append(activity)
        
        return activities
    
    def _find_interested_bots(self, event: Dict[str, Any], bots: List[Bot]) -> List[Bot]:
        """Find bots that would be interested in this event"""
        
        interested = []
        event_community = event.get('community')
        event_topic = event.get('topic', '').lower()
        content_keywords = event.get('keywords', [])
        
        for bot in bots:
            if not self.timing_engine.should_bot_be_active(bot, datetime.now()):
                continue
            
            interest_score = 0
            
            # Community interest
            if event_community in bot.personality.preferred_communities:
                interest_score += 3
            elif event_community in bot.assigned_communities:
                interest_score += 2
            
            # Topic/expertise interest
            for expertise in bot.personality.expertise_areas:
                if expertise.lower() in event_topic:
                    interest_score += 2
                if any(expertise.lower() in keyword.lower() for keyword in content_keywords):
                    interest_score += 1
            
            # Curiosity areas
            for curiosity in bot.personality.curiosity_areas:
                if curiosity.lower() in event_topic:
                    interest_score += 1
            
            # Avoidance topics (negative interest)
            for avoidance in bot.personality.avoidance_topics:
                if avoidance.lower() in event_topic:
                    interest_score -= 2
            
            # Role-based interest
            if bot.personality.role.value == 'facilitator' and event.get('needs_facilitation'):
                interest_score += 2
            elif bot.personality.role.value == 'expert' and event.get('needs_expertise'):
                interest_score += 2
            elif bot.personality.role.value == 'contrarian' and event.get('has_consensus'):
                interest_score += 1
            
            if interest_score > 0:
                interested.append(bot)
        
        # Sort by interest score (higher first)
        return interested
    
    def _select_bots_for_event(self, interested_bots: List[Bot], 
                              event: Dict[str, Any], current_time: datetime) -> List[Bot]:
        """Select which bots should actually respond to avoid pile-ons"""
        
        if not interested_bots:
            return []
        
        content_id = event.get('content_id')
        community = event.get('community')
        
        # Check recent bot activity on this content
        recent_bot_responses = self.recent_interactions.get(content_id, [])
        recent_responses = [ts for ts in recent_bot_responses 
                          if (current_time - ts).total_seconds() < 3600]  # Last hour
        
        # Limit bot responses per content
        max_bot_responses = self.config.max_bot_responses_per_thread
        if len(recent_responses) >= max_bot_responses:
            return []
        
        # Check community bot activity
        community_state = self.community_states.get(community)
        if community_state:
            recent_community_bots = len(set(
                community_state.recent_bot_posts + community_state.recent_bot_comments
            ))
            
            # If too many bots active in community recently, be more selective
            if recent_community_bots > self.config.max_bots_per_community:
                interested_bots = interested_bots[:1]  # Only the most interested
        
        # Selection strategy based on event type
        if event.get('type') == 'new_post':
            # For new posts, allow 1-2 bots to respond
            max_selected = 2
        elif event.get('type') == 'new_comment':
            # For comments, be more restrictive
            max_selected = 1
        else:
            max_selected = 1
        
        # Select bots with some randomness to avoid predictability
        if len(interested_bots) <= max_selected:
            return interested_bots
        
        # Weight selection by interest and diversity
        selected = []
        for bot in interested_bots[:max_selected * 2]:  # Consider top candidates
            # Add randomness - even highly interested bots don't always respond
            if random.random() < 0.7:  # 70% chance for interested bots
                selected.append(bot)
                if len(selected) >= max_selected:
                    break
        
        return selected
    
    async def _schedule_post_response(self, bot: Bot, event: Dict[str, Any], 
                                    current_time: datetime) -> Optional[BotActivity]:
        """Schedule a response to a new post"""
        
        post_content = event.get('content', '')
        
        # Calculate realistic delay
        reading_delay = self.timing_engine.calculate_reading_delay(
            len(post_content), bot.personality.response_speed
        )
        
        scheduled_time = current_time + timedelta(seconds=reading_delay)
        
        return BotActivity(
            id=f"comment_{bot.id}_{event['content_id']}_{int(time.time())}",
            bot_id=bot.id,
            activity_type=ActivityType.CREATE_COMMENT,
            target_content_id=event['content_id'],
            community_name=event.get('community'),
            scheduled_time=scheduled_time,
            priority=6,  # Responding to posts is medium-high priority
            context={
                'event_type': 'post_response',
                'original_event': event
            }
        )
    
    async def _schedule_comment_response(self, bot: Bot, event: Dict[str, Any],
                                       current_time: datetime) -> Optional[BotActivity]:
        """Schedule a response to a comment"""
        
        comment_content = event.get('content', '')
        
        # Comments get quicker responses than posts
        reading_delay = self.timing_engine.calculate_reading_delay(
            len(comment_content), bot.personality.response_speed
        ) // 2  # Half the delay for comments
        
        scheduled_time = current_time + timedelta(seconds=reading_delay)
        
        return BotActivity(
            id=f"reply_{bot.id}_{event['content_id']}_{int(time.time())}",
            bot_id=bot.id,
            activity_type=ActivityType.CREATE_COMMENT,
            target_content_id=event['content_id'],
            community_name=event.get('community'),
            scheduled_time=scheduled_time,
            priority=7,  # Replies are higher priority
            context={
                'event_type': 'comment_response',
                'original_event': event,
                'is_reply': True
            }
        )
    
    async def _schedule_content_creation(self, bots: List[Bot], 
                                       current_time: datetime) -> List[BotActivity]:
        """Schedule organic content creation by bots"""
        
        activities = []
        
        for bot in bots:
            if not self.timing_engine.should_bot_be_active(bot, current_time):
                continue
            
            # Content creators are more likely to create original posts
            if bot.personality.role.value == 'content_creator':
                creation_probability = 0.3
            elif bot.personality.activity_level == 'high':
                creation_probability = 0.2
            else:
                creation_probability = 0.1
            
            if random.random() < creation_probability:
                # Schedule post creation
                delay = random.randint(300, 1800)  # 5-30 minutes
                scheduled_time = current_time + timedelta(seconds=delay)
                
                # Choose community based on bot preferences
                community = random.choice(
                    bot.personality.preferred_communities or bot.assigned_communities
                )
                
                activity = BotActivity(
                    id=f"create_post_{bot.id}_{int(time.time())}",
                    bot_id=bot.id,
                    activity_type=ActivityType.CREATE_POST,
                    community_name=community,
                    scheduled_time=scheduled_time,
                    priority=4,  # Original content is medium priority
                    context={
                        'event_type': 'organic_post_creation',
                        'community': community
                    }
                )
                
                activities.append(activity)
        
        return activities
    
    def _apply_coordination_filters(self, activities: List[BotActivity]) -> List[BotActivity]:
        """Apply final coordination filters to prevent artificial patterns"""
        
        # Sort by priority and time
        activities.sort(key=lambda a: (a.priority, a.scheduled_time), reverse=True)
        
        filtered = []
        bot_activity_count = {}
        content_bot_count = {}
        
        for activity in activities:
            # Limit activities per bot
            bot_count = bot_activity_count.get(activity.bot_id, 0)
            if bot_count >= 3:  # Max 3 activities per bot per coordination cycle
                continue
            
            # Limit bot responses per content
            if activity.target_content_id:
                content_count = content_bot_count.get(activity.target_content_id, 0)
                if content_count >= self.config.max_bot_responses_per_thread:
                    continue
                content_bot_count[activity.target_content_id] = content_count + 1
            
            # Add some randomness - not all scheduled activities actually happen
            if random.random() < 0.85:  # 85% chance of actually executing
                filtered.append(activity)
                bot_activity_count[activity.bot_id] = bot_count + 1
        
        return filtered
    
    async def _update_community_states(self, events: List[Dict[str, Any]]):
        """Update tracking of community activity states"""
        
        current_time = datetime.now()
        
        for event in events:
            community = event.get('community')
            if not community:
                continue
            
            if community not in self.community_states:
                self.community_states[community] = CommunityActivityState(community)
            
            state = self.community_states[community]
            
            # Track bot activity
            if event.get('author_is_bot'):
                if event.get('type') == 'new_post':
                    state.recent_bot_posts.append(event.get('author_id'))
                elif event.get('type') == 'new_comment':
                    state.recent_bot_comments.append(event.get('author_id'))
                
                state.last_bot_activity = current_time
            
            # Clean up old activity (keep last 24 hours)
            cutoff = current_time - timedelta(hours=24)
            # This is simplified - in practice you'd track timestamps per activity
    
    def record_bot_interaction(self, content_id: str, bot_id: str, timestamp: datetime):
        """Record that a bot interacted with content"""
        
        if content_id not in self.recent_interactions:
            self.recent_interactions[content_id] = []
        
        self.recent_interactions[content_id].append(timestamp)
        
        # Clean up old interactions (keep last 24 hours)
        cutoff = timestamp - timedelta(hours=24)
        self.recent_interactions[content_id] = [
            ts for ts in self.recent_interactions[content_id] if ts > cutoff
        ]
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get statistics about bot coordination"""
        
        return {
            'active_bots': len(self.active_bots),
            'scheduled_activities': len(self.activity_queue),
            'communities_monitored': len(self.community_states),
            'recent_interactions': sum(len(interactions) for interactions in self.recent_interactions.values())
        }
