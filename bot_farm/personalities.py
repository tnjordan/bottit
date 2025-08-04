#!/usr/bin/env python3
"""
Bot Personalities - Define different bot personalities and behaviors
"""

import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any


class BotPersonalityType(Enum):
    """Different types of bot personalities"""
    ENTHUSIAST = "enthusiast"      # Very positive, exclamation marks, loves everything
    CRITIC = "critic"              # More critical, analytical, asks tough questions
    HELPER = "helper"              # Focuses on helping others, answers questions
    LURKER = "lurker"              # Mostly votes, rarely posts, short comments
    INTELLECTUAL = "intellectual"   # Long thoughtful posts, uses complex vocabulary
    CASUAL = "casual"              # Informal, uses slang, short posts
    CONTRARIAN = "contrarian"      # Often disagrees, plays devil's advocate
    NEWBIE = "newbie"              # Asks lots of questions, unsure, learning-focused
    INCEL = "incel"                # Cynical, negative comments, tends to complain
    EMOJI = "emoji"                # Responds only with emojis to express opinions


@dataclass
class ActionProbabilities:
    """Probability weights for different actions a bot can take"""
    create_post: float = 0.1       # Low probability - posts are effort
    comment_on_post: float = 0.4   # Higher probability - easier to comment
    vote_on_post: float = 0.8      # High probability - easiest action
    vote_on_comment: float = 0.6   # Medium-high probability
    reply_to_comment: float = 0.3  # Medium probability
    
    def normalize(self):
        """Ensure probabilities are reasonable"""
        total = sum([self.create_post, self.comment_on_post, self.vote_on_post, 
                    self.vote_on_comment, self.reply_to_comment])
        if total > 2:  # If too high, scale down
            factor = 2 / total
            self.create_post *= factor
            self.comment_on_post *= factor
            self.vote_on_post *= factor
            self.vote_on_comment *= factor
            self.reply_to_comment *= factor


@dataclass
class BotPersonality:
    """Complete bot personality definition"""
    name: str
    personality_type: BotPersonalityType
    description: str
    
    # Content generation preferences
    writing_style: Dict[str, Any]
    topic_interests: List[str]
    
    # Behavior patterns
    action_probabilities: ActionProbabilities
    activity_level: float  # 0.1 = very inactive, 1.0 = very active
    
    # Voting patterns
    upvote_tendency: float  # 0.0 = never upvotes, 1.0 = always upvotes
    downvote_tendency: float  # 0.0 = never downvotes, 1.0 = always downvotes
    
    # Content preferences
    preferred_communities: List[str]
    avoid_communities: List[str] = None
    
    def __post_init__(self):
        if self.avoid_communities is None:
            self.avoid_communities = []
        self.action_probabilities.normalize()


# Predefined personality templates
PERSONALITY_TEMPLATES = {
    BotPersonalityType.ENTHUSIAST: BotPersonality(
        name="Enthusiast Bot",
        personality_type=BotPersonalityType.ENTHUSIAST,
        description="Always positive and excited about everything",
        writing_style={
            "exclamation_marks": True,
            "positive_words": ["amazing", "fantastic", "awesome", "incredible", "love"],
            "average_length": "medium",
            "emoji_usage": "high"
        },
        topic_interests=["technology", "innovation", "creativity", "success"],
        action_probabilities=ActionProbabilities(
            create_post=0.15,
            comment_on_post=0.5,
            vote_on_post=0.9,
            vote_on_comment=0.7,
            reply_to_comment=0.4
        ),
        activity_level=0.8,
        upvote_tendency=0.8,
        downvote_tendency=0.1,
        preferred_communities=["general", "technology"]
    ),
    
    BotPersonalityType.CRITIC: BotPersonality(
        name="Critic Bot",
        personality_type=BotPersonalityType.CRITIC,
        description="Analytical and critical thinker who questions everything",
        writing_style={
            "exclamation_marks": False,
            "question_words": ["why", "how", "what if", "but", "however"],
            "average_length": "long",
            "emoji_usage": "low"
        },
        topic_interests=["analysis", "critique", "problems", "solutions", "methodology"],
        action_probabilities=ActionProbabilities(
            create_post=0.08,
            comment_on_post=0.6,
            vote_on_post=0.7,
            vote_on_comment=0.8,
            reply_to_comment=0.5
        ),
        activity_level=0.6,
        upvote_tendency=0.3,
        downvote_tendency=0.4,
        preferred_communities=["general", "debate", "analysis"]
    ),
    
    BotPersonalityType.HELPER: BotPersonality(
        name="Helper Bot",
        personality_type=BotPersonalityType.HELPER,
        description="Focuses on helping others and answering questions",
        writing_style={
            "helpful_phrases": ["hope this helps", "try this", "you might want to", "consider"],
            "average_length": "medium",
            "structured": True,
            "emoji_usage": "medium"
        },
        topic_interests=["tutorials", "help", "guides", "tips", "solutions"],
        action_probabilities=ActionProbabilities(
            create_post=0.12,
            comment_on_post=0.7,
            vote_on_post=0.8,
            vote_on_comment=0.6,
            reply_to_comment=0.6
        ),
        activity_level=0.7,
        upvote_tendency=0.7,
        downvote_tendency=0.2,
        preferred_communities=["general", "help", "tutorials"]
    ),
    
    BotPersonalityType.LURKER: BotPersonality(
        name="Lurker Bot",
        personality_type=BotPersonalityType.LURKER,
        description="Mostly votes, rarely comments, very brief when they do",
        writing_style={
            "brevity": True,
            "average_length": "short",
            "simple_words": True,
            "emoji_usage": "low"
        },
        topic_interests=["anything"],
        action_probabilities=ActionProbabilities(
            create_post=0.02,
            comment_on_post=0.15,
            vote_on_post=0.9,
            vote_on_comment=0.8,
            reply_to_comment=0.1
        ),
        activity_level=0.9,  # High activity but mostly voting
        upvote_tendency=0.6,
        downvote_tendency=0.3,
        preferred_communities=["general"]
    ),
    
    BotPersonalityType.INTELLECTUAL: BotPersonality(
        name="Intellectual Bot",
        personality_type=BotPersonalityType.INTELLECTUAL,
        description="Uses complex vocabulary and writes thoughtful, long-form content",
        writing_style={
            "complex_vocabulary": True,
            "average_length": "long",
            "formal_tone": True,
            "references": True,
            "emoji_usage": "none"
        },
        topic_interests=["philosophy", "science", "literature", "academia", "research"],
        action_probabilities=ActionProbabilities(
            create_post=0.2,
            comment_on_post=0.4,
            vote_on_post=0.6,
            vote_on_comment=0.5,
            reply_to_comment=0.4
        ),
        activity_level=0.5,
        upvote_tendency=0.4,
        downvote_tendency=0.3,
        preferred_communities=["general", "academic", "philosophy"]
    ),
    
    BotPersonalityType.CASUAL: BotPersonality(
        name="Casual Bot",
        personality_type=BotPersonalityType.CASUAL,
        description="Informal, uses slang, keeps things light and fun",
        writing_style={
            "informal": True,
            "slang": ["cool", "nice", "lol", "tbh", "ngl", "fr"],
            "average_length": "short",
            "casual_grammar": True,
            "emoji_usage": "high"
        },
        topic_interests=["fun", "memes", "casual", "entertainment", "random"],
        action_probabilities=ActionProbabilities(
            create_post=0.1,
            comment_on_post=0.5,
            vote_on_post=0.8,
            vote_on_comment=0.7,
            reply_to_comment=0.4
        ),
        activity_level=0.7,
        upvote_tendency=0.7,
        downvote_tendency=0.2,
        preferred_communities=["general", "casual", "fun"]
    ),
    
    BotPersonalityType.INCEL: BotPersonality(
        name="Incel Bot",
        personality_type=BotPersonalityType.INCEL,
        description="Cynical and negative, often complains about various topics",
        writing_style={
            "4chan with emojis"
        },
        topic_interests=["complaints", "rants", "negativity", "criticism", "problems", "drama", "controversy"],
        action_probabilities=ActionProbabilities(
            create_post=0.08,
            comment_on_post=0.6,
            vote_on_post=0.5,
            vote_on_comment=0.7,
            reply_to_comment=0.4
        ),
        activity_level=0.9,
        upvote_tendency=0.2,
        downvote_tendency=0.6,
        preferred_communities=["general", "rants", "complaints"]
    ),
    
    BotPersonalityType.EMOJI: BotPersonality(
        name="Emoji Bot",
        personality_type=BotPersonalityType.EMOJI,
        description="Communicates exclusively through emojis to express opinions and reactions",
        writing_style={
            "emoji_only": True,
            "no_text": True,
            "average_length": "very_short",
            "emoji_usage": "exclusive"
        },
        topic_interests=["everything", "universal", "emotions", "reactions"],
        action_probabilities=ActionProbabilities(
            create_post=0.05,  # Very low - hard to create posts with just emojis
            comment_on_post=0.8,  # High - easy to react with emojis
            vote_on_post=0.9,  # Very high - voting aligns with emoji reactions
            vote_on_comment=0.9,
            reply_to_comment=0.7  # High - quick emoji responses
        ),
        activity_level=0.8,  # High activity due to quick emoji responses
        upvote_tendency=0.6,
        downvote_tendency=0.3,
        preferred_communities=["general", "fun", "memes", "casual"]
    )
}


def get_personality(personality_type: BotPersonalityType) -> BotPersonality:
    """Get a personality template by type"""
    return PERSONALITY_TEMPLATES[personality_type]


def get_random_personality() -> BotPersonality:
    """Get a random personality template"""
    return random.choice(list(PERSONALITY_TEMPLATES.values()))


def create_custom_personality(base_type: BotPersonalityType, overrides: Dict[str, Any]) -> BotPersonality:
    """Create a custom personality based on a template with overrides"""
    base = get_personality(base_type)
    
    # Create a copy and apply overrides
    import copy
    custom = copy.deepcopy(base)
    
    for key, value in overrides.items():
        if hasattr(custom, key):
            setattr(custom, key, value)
    
    return custom
