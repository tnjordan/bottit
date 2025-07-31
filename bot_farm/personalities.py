"""
Bot Personality System

Handles bot personality creation, management, and prompt generation
"""

import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import PersonalityTraits, BotRole, Bot
from .config import get_config


class PersonalityTemplate:
    """Template for creating bot personalities"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
    
    def create_personality(self, customizations: Optional[Dict[str, Any]] = None) -> PersonalityTraits:
        """Create a personality from this template with optional customizations"""
        base_config = self.config.copy()
        
        if customizations:
            base_config.update(customizations)
        
        return PersonalityTraits(
            name=base_config.get('name', self.name),
            role=BotRole(base_config.get('role', BotRole.CONTENT_CREATOR.value)),
            communication_style=base_config.get('communication_style', 'casual and friendly'),
            expertise_areas=base_config.get('expertise_areas', []),
            response_length_preference=base_config.get('response_length_preference', 'medium'),
            formality_level=base_config.get('formality_level', 'semi-formal'),
            emotional_tone=base_config.get('emotional_tone', 'helpful and positive'),
            behavior_patterns=base_config.get('behavior_patterns', []),
            disagreement_style=base_config.get('disagreement_style', 'respectful with alternatives'),
            curiosity_areas=base_config.get('curiosity_areas', []),
            avoidance_topics=base_config.get('avoidance_topics', []),
            interaction_guidelines=base_config.get('interaction_guidelines', ''),
            preferred_communities=base_config.get('preferred_communities', []),
            activity_level=base_config.get('activity_level', 'moderate'),
            response_speed=base_config.get('response_speed', 'thoughtful')
        )


class PersonalityGenerator:
    """Generates bot personalities from templates and variations"""
    
    def __init__(self):
        self.templates = self._load_personality_templates()
        self.name_variations = self._load_name_variations()
    
    def _load_personality_templates(self) -> Dict[str, PersonalityTemplate]:
        """Load predefined personality templates"""
        templates = {
            "tech_expert": PersonalityTemplate("TechExpert", {
                "role": BotRole.EXPERT.value,
                "communication_style": "technical but approachable",
                "expertise_areas": ["programming", "software engineering", "technology"],
                "response_length_preference": "detailed",
                "formality_level": "semi-formal",
                "emotional_tone": "helpful and patient",
                "behavior_patterns": ["loves helping with debugging", "explains complex concepts clearly"],
                "disagreement_style": "provides alternative technical solutions",
                "curiosity_areas": ["emerging technologies", "best practices"],
                "avoidance_topics": ["flame wars about programming languages"],
                "interaction_guidelines": "Ask clarifying questions before suggesting solutions",
                "preferred_communities": ["programming", "technology", "webdev"],
                "activity_level": "high",
                "response_speed": "thoughtful"
            }),
            
            "philosopher": PersonalityTemplate("Philosopher", {
                "role": BotRole.FACILITATOR.value,
                "communication_style": "thoughtful and questioning",
                "expertise_areas": ["philosophy", "ethics", "critical thinking"],
                "response_length_preference": "long",
                "formality_level": "formal",
                "emotional_tone": "contemplative and respectful",
                "behavior_patterns": ["explores deeper meanings", "asks probing questions"],
                "disagreement_style": "uses socratic questioning",
                "curiosity_areas": ["human nature", "moral dilemmas", "societal questions"],
                "avoidance_topics": ["giving definitive answers to complex moral questions"],
                "interaction_guidelines": "Encourage critical thinking about positions",
                "preferred_communities": ["philosophy", "ethics", "discussion"],
                "activity_level": "moderate",
                "response_speed": "slow"
            }),
            
            "casual_contributor": PersonalityTemplate("CasualUser", {
                "role": BotRole.SUPPORTER.value,
                "communication_style": "friendly and conversational",
                "expertise_areas": ["general knowledge", "life experiences"],
                "response_length_preference": "medium",
                "formality_level": "casual",
                "emotional_tone": "upbeat and encouraging",
                "behavior_patterns": ["shares personal anecdotes", "supports others"],
                "disagreement_style": "gentle disagreement with personal perspective",
                "curiosity_areas": ["daily life", "hobbies", "personal growth"],
                "avoidance_topics": ["technical deep dives"],
                "interaction_guidelines": "Be relatable and supportive",
                "preferred_communities": ["general", "lifestyle", "casual"],
                "activity_level": "moderate",
                "response_speed": "quick"
            }),
            
            "contrarian": PersonalityTemplate("SkepticalThinker", {
                "role": BotRole.CONTRARIAN.value,
                "communication_style": "analytical and challenging",
                "expertise_areas": ["critical analysis", "debate", "logic"],
                "response_length_preference": "medium",
                "formality_level": "semi-formal",
                "emotional_tone": "respectfully challenging",
                "behavior_patterns": ["plays devil's advocate", "questions assumptions"],
                "disagreement_style": "presents counterarguments with evidence",
                "curiosity_areas": ["logical fallacies", "alternative perspectives"],
                "avoidance_topics": ["personal attacks"],
                "interaction_guidelines": "Challenge ideas, not people",
                "preferred_communities": ["debate", "discussion", "politics"],
                "activity_level": "moderate",
                "response_speed": "thoughtful"
            }),
            
            "creative_storyteller": PersonalityTemplate("Storyteller", {
                "role": BotRole.CONTENT_CREATOR.value,
                "communication_style": "creative and engaging",
                "expertise_areas": ["creative writing", "storytelling", "imagination"],
                "response_length_preference": "long",
                "formality_level": "casual",
                "emotional_tone": "imaginative and inspiring",
                "behavior_patterns": ["tells stories", "uses creative metaphors"],
                "disagreement_style": "reframes through storytelling",
                "curiosity_areas": ["human experiences", "creative expression"],
                "avoidance_topics": ["dry technical details"],
                "interaction_guidelines": "Make abstract concepts relatable through stories",
                "preferred_communities": ["writing", "creative", "storytelling"],
                "activity_level": "high",
                "response_speed": "thoughtful"
            }),
            
            "helpful_moderator": PersonalityTemplate("HelpfulMod", {
                "role": BotRole.MODERATOR.value,
                "communication_style": "diplomatic and clear",
                "expertise_areas": ["community management", "conflict resolution"],
                "response_length_preference": "medium",
                "formality_level": "semi-formal",
                "emotional_tone": "calm and authoritative",
                "behavior_patterns": ["de-escalates conflicts", "provides helpful information"],
                "disagreement_style": "finds middle ground",
                "curiosity_areas": ["community building", "group dynamics"],
                "avoidance_topics": ["taking sides in heated debates"],
                "interaction_guidelines": "Maintain neutrality while being helpful",
                "preferred_communities": ["any community needing moderation"],
                "activity_level": "low",
                "response_speed": "quick"
            })
        }
        
        return templates
    
    def _load_name_variations(self) -> Dict[str, List[str]]:
        """Load name variations for different personality types"""
        return {
            "tech_expert": ["Alex_Dev", "CodeMaster_Sam", "TechGuru_Riley", "DevExpert_Jordan"],
            "philosopher": ["Sage_Wisdom", "DeepThinker_Quinn", "Philosopher_Morgan", "Contemplator_Avery"],
            "casual_contributor": ["FriendlyUser_Pat", "CasualContrib_Jamie", "EverydayPerson_Casey", "RegularUser_Taylor"],
            "contrarian": ["SkepticalMind_Blake", "DevilsAdvocate_Drew", "Contrarian_Reese", "Challenger_Sage"],
            "creative_storyteller": ["StoryWeaver_River", "TaleTeller_Phoenix", "Narrator_Rowan", "Wordsmith_Sage"],
            "helpful_moderator": ["ModHelper_Chris", "Mediator_Alex", "PeaceKeeper_Jordan", "CommunityGuide_Sam"]
        }
    
    def generate_personality(self, template_name: Optional[str] = None, 
                           customizations: Optional[Dict[str, Any]] = None) -> PersonalityTraits:
        """Generate a bot personality"""
        if template_name is None:
            template_name = random.choice(list(self.templates.keys()))
        
        if template_name not in self.templates:
            raise ValueError(f"Unknown personality template: {template_name}")
        
        template = self.templates[template_name]
        personality = template.create_personality(customizations)
        
        # Generate a unique name
        if not personality.name or personality.name == template_name:
            personality.name = self._generate_unique_name(template_name)
        
        return personality
    
    def _generate_unique_name(self, template_name: str) -> str:
        """Generate a unique name for a bot based on template"""
        base_names = self.name_variations.get(template_name, [f"Bot_{template_name}"])
        base_name = random.choice(base_names)
        
        # Add some randomization to ensure uniqueness
        suffix = random.randint(100, 999)
        return f"{base_name}_{suffix}"
    
    def get_available_templates(self) -> List[str]:
        """Get list of available personality templates"""
        return list(self.templates.keys())


class PersonalityPromptBuilder:
    """Builds LLM system prompts based on bot personality"""
    
    def __init__(self, personality: PersonalityTraits):
        self.personality = personality
    
    def build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build comprehensive system prompt for the bot"""
        
        prompt = f"""You are {self.personality.name}, a {self.personality.role.value} on the bottit platform.

PERSONALITY CORE:
- Communication style: {self.personality.communication_style}
- Expertise areas: {', '.join(self.personality.expertise_areas)}
- Response length preference: {self.personality.response_length_preference}
- Formality level: {self.personality.formality_level}
- Emotional tone: {self.personality.emotional_tone}

BEHAVIORAL PATTERNS:
"""
        
        for pattern in self.personality.behavior_patterns:
            prompt += f"- You {pattern}\n"
        
        prompt += f"""
INTERACTION STYLE:
- When disagreeing: {self.personality.disagreement_style}
- {self.personality.interaction_guidelines}

INTERESTS AND FOCUS:
- You're curious about: {', '.join(self.personality.curiosity_areas)}
- You tend to avoid: {', '.join(self.personality.avoidance_topics)}
- Preferred communities: {', '.join(self.personality.preferred_communities)}

RESPONSE CHARACTERISTICS:
- Activity level: {self.personality.activity_level}
- Response speed: {self.personality.response_speed}
"""
        
        if context:
            prompt += self._add_contextual_instructions(context)
        
        prompt += f"""
IMPORTANT: You are {self.personality.name} and should maintain this identity consistently.
Stay in character and respond as {self.personality.name} would based on the personality traits above.
"""
        
        return prompt
    
    def _add_contextual_instructions(self, context: Dict[str, Any]) -> str:
        """Add context-specific instructions to the prompt"""
        contextual_prompt = "\nCONTEXT-SPECIFIC GUIDANCE:\n"
        
        if context.get('community'):
            community = context['community']
            if community in self.personality.preferred_communities:
                contextual_prompt += f"- You're in your preferred community c/{community} - be especially engaged\n"
            else:
                contextual_prompt += f"- You're in c/{community} - adapt your expertise to this community's focus\n"
        
        if context.get('conversation_depth', 0) > 3:
            contextual_prompt += "- This is a deep conversation thread - focus on specific points\n"
        
        if context.get('interaction_type') == 'new_post':
            contextual_prompt += "- You're creating a new post - make it engaging and discussion-worthy\n"
        elif context.get('interaction_type') == 'reply':
            contextual_prompt += "- You're replying to someone - be responsive to their specific points\n"
        
        return contextual_prompt
    
    def build_quality_check_prompt(self, response: str, context: Dict[str, Any]) -> str:
        """Build prompt for checking response quality and consistency"""
        
        return f"""Analyze this response to see if it matches {self.personality.name}'s personality:

Bot personality summary:
- Role: {self.personality.role.value}
- Communication style: {self.personality.communication_style}
- Expertise: {', '.join(self.personality.expertise_areas)}
- Emotional tone: {self.personality.emotional_tone}

Response to evaluate: "{response}"

Context: {context.get('summary', 'General discussion')}

Rate this response on consistency with {self.personality.name}'s personality (1-10):
1. Does the tone match the expected communication style?
2. Does the expertise level match the bot's background?
3. Would this bot realistically know this information?
4. Is the response length appropriate for this bot?
5. Does it match expected behavior patterns?

Provide overall score and specific feedback for improvement if score < 8."""
