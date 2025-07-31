"""
Bot Factory System

Creates and manages bot instances with unique personalities and configurations
"""

import asyncio
import random
import string
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from .models import Bot, PersonalityTraits, BotRole, BotStatus
from .personalities import PersonalityGenerator
from .config import get_config, LLMProvider


class BotNameGenerator:
    """Generates unique and realistic bot names"""
    
    def __init__(self):
        self.used_names: set = set()
        self.name_components = self._load_name_components()
    
    def _load_name_components(self) -> Dict[str, List[str]]:
        """Load components for generating bot names"""
        return {
            'tech_prefixes': [
                'Code', 'Dev', 'Tech', 'Cyber', 'Digital', 'Byte', 'Pixel', 'Logic',
                'Data', 'Net', 'Web', 'App', 'API', 'Git', 'Stack', 'Cloud'
            ],
            'tech_suffixes': [
                'Master', 'Guru', 'Expert', 'Ninja', 'Wizard', 'Coder', 'Builder',
                'Hacker', 'Engineer', 'Architect', 'Developer', 'Geek'
            ],
            'casual_prefixes': [
                'Friendly', 'Casual', 'Regular', 'Everyday', 'Simple', 'Easy',
                'Chill', 'Laid', 'Cool', 'Nice', 'Kind', 'Helpful'
            ],
            'casual_suffixes': [
                'User', 'Person', 'Contributor', 'Member', 'Friend', 'Buddy',
                'Pal', 'Helper', 'Supporter', 'Participant'
            ],
            'creative_prefixes': [
                'Story', 'Tale', 'Word', 'Creative', 'Imaginative', 'Artistic',
                'Expressive', 'Narrative', 'Poetic', 'Literary'
            ],
            'creative_suffixes': [
                'Teller', 'Weaver', 'Smith', 'Crafter', 'Maker', 'Builder',
                'Writer', 'Author', 'Creator', 'Artist'
            ],
            'philosophical_prefixes': [
                'Deep', 'Wise', 'Thoughtful', 'Contemplative', 'Reflective',
                'Philosophical', 'Intellectual', 'Sage', 'Mind', 'Soul'
            ],
            'philosophical_suffixes': [
                'Thinker', 'Philosopher', 'Sage', 'Wisdom', 'Mind', 'Seeker',
                'Questioner', 'Contemplator', 'Ponderer', 'Scholar'
            ],
            'common_names': [
                'Alex', 'Jordan', 'Taylor', 'Casey', 'Riley', 'Morgan', 'Avery',
                'Quinn', 'Blake', 'Drew', 'Sage', 'River', 'Phoenix', 'Rowan'
            ]
        }
    
    def generate_name(self, personality_type: str, role: BotRole) -> str:
        """Generate a unique name based on personality type and role"""
        
        # Choose name components based on role
        if role == BotRole.EXPERT and 'tech' in personality_type.lower():
            prefixes = self.name_components['tech_prefixes']
            suffixes = self.name_components['tech_suffixes']
        elif role == BotRole.CONTENT_CREATOR and 'creative' in personality_type.lower():
            prefixes = self.name_components['creative_prefixes']
            suffixes = self.name_components['creative_suffixes']
        elif role == BotRole.FACILITATOR and 'philosoph' in personality_type.lower():
            prefixes = self.name_components['philosophical_prefixes']
            suffixes = self.name_components['philosophical_suffixes']
        elif role in [BotRole.SUPPORTER, BotRole.LURKER]:
            prefixes = self.name_components['casual_prefixes']
            suffixes = self.name_components['casual_suffixes']
        else:
            # Mix different types for variety
            all_prefixes = []
            all_suffixes = []
            for key in self.name_components:
                if 'prefix' in key:
                    all_prefixes.extend(self.name_components[key])
                elif 'suffix' in key:
                    all_suffixes.extend(self.name_components[key])
            prefixes = all_prefixes
            suffixes = all_suffixes
        
        # Generate name variations
        attempts = 0
        while attempts < 50:  # Prevent infinite loops
            
            name_style = random.choice(['compound', 'underscore', 'simple'])
            
            if name_style == 'compound':
                # CompoundName style
                prefix = random.choice(prefixes)
                suffix = random.choice(suffixes)
                name = f"{prefix}{suffix}"
            
            elif name_style == 'underscore':
                # Prefix_Suffix style
                prefix = random.choice(prefixes)
                suffix = random.choice(suffixes)
                name = f"{prefix}_{suffix}"
            
            else:  # simple
                # Just use a common name with a role indicator
                base_name = random.choice(self.name_components['common_names'])
                role_indicator = random.choice(suffixes)
                name = f"{base_name}_{role_indicator}"
            
            # Add number suffix if needed for uniqueness
            if name in self.used_names:
                number = random.randint(10, 999)
                name = f"{name}_{number}"
            
            if name not in self.used_names:
                self.used_names.add(name)
                return name
            
            attempts += 1
        
        # Fallback to UUID-based name if all else fails
        fallback_name = f"Bot_{str(uuid.uuid4())[:8]}"
        self.used_names.add(fallback_name)
        return fallback_name
    
    def is_name_available(self, name: str) -> bool:
        """Check if a name is available"""
        return name not in self.used_names
    
    def reserve_name(self, name: str):
        """Reserve a name to prevent duplicates"""
        self.used_names.add(name)


class BotSpecificationBuilder:
    """Builds bot specifications based on platform needs"""
    
    def __init__(self):
        self.config = get_config()
    
    def build_spec_for_inactive_community(self, community_name: str,
                                        community_info: Dict[str, Any]) -> Dict[str, Any]:
        """Build bot spec to help inactive community"""
        
        return {
            'creation_reason': f'Activate community c/{community_name}',
            'role': BotRole.CONTENT_CREATOR,
            'primary_communities': [community_name],
            'personality_customizations': {
                'activity_level': 'high',
                'preferred_communities': [community_name],
                'behavior_patterns': [
                    'creates engaging discussion topics',
                    'asks thoughtful questions',
                    'welcomes new community members'
                ]
            },
            'llm_provider': LLMProvider.GOOGLE,
            'priority': 8  # High priority for community health
        }
    
    def build_spec_for_expertise_gap(self, topic: str, 
                                   communities: List[str]) -> Dict[str, Any]:
        """Build bot spec to fill expertise gap"""
        
        return {
            'creation_reason': f'Provide expertise in {topic}',
            'role': BotRole.EXPERT,
            'primary_communities': communities,
            'personality_customizations': {
                'expertise_areas': [topic],
                'response_length_preference': 'detailed',
                'behavior_patterns': [
                    'provides detailed explanations',
                    'shares practical examples',
                    'helps solve complex problems'
                ],
                'interaction_guidelines': f'Focus on helping others learn {topic}'
            },
            'llm_provider': LLMProvider.GOOGLE,  # Use Google for expertise
            'priority': 7
        }
    
    def build_spec_for_discussion_facilitation(self, community_name: str) -> Dict[str, Any]:
        """Build bot spec to improve discussion quality"""
        
        return {
            'creation_reason': f'Facilitate discussions in c/{community_name}',
            'role': BotRole.FACILITATOR,
            'primary_communities': [community_name],
            'personality_customizations': {
                'behavior_patterns': [
                    'asks follow-up questions',
                    'encourages different perspectives',
                    'summarizes complex discussions'
                ],
                'disagreement_style': 'finds common ground',
                'interaction_guidelines': 'Help others explore ideas more deeply'
            },
            'llm_provider': LLMProvider.GOOGLE,  # Good for nuanced discussion
            'priority': 6
        }
    
    def build_spec_for_community_balance(self, community_name: str,
                                       needed_perspective: str) -> Dict[str, Any]:
        """Build bot spec to balance community perspectives"""
        
        role = BotRole.CONTRARIAN if needed_perspective == 'contrarian' else BotRole.SUPPORTER
        
        return {
            'creation_reason': f'Balance perspectives in c/{community_name}',
            'role': role,
            'primary_communities': [community_name],
            'personality_customizations': {
                'behavior_patterns': [
                    f'provides {needed_perspective} viewpoints',
                    'challenges assumptions respectfully',
                    'promotes critical thinking'
                ] if role == BotRole.CONTRARIAN else [
                    'supports good ideas',
                    'encourages participation',
                    'builds on others\' contributions'
                ]
            },
            'llm_provider': LLMProvider.GOOGLE,  # Fast responses for interaction
            'priority': 5
        }
    
    def build_random_spec(self) -> Dict[str, Any]:
        """Build a random bot spec for organic diversity"""
        
        roles = list(BotRole)
        role = random.choice(roles)
        
        # Get random personality template
        personality_generator = PersonalityGenerator()
        templates = personality_generator.get_available_templates()
        template = random.choice(templates)
        
        # Use Google as the only provider
        provider = LLMProvider.GOOGLE
        
        return {
            'creation_reason': 'Organic bot diversity',
            'role': role,
            'personality_template': template,
            'llm_provider': provider,
            'priority': 3  # Lower priority for random bots
        }


class BotFactory:
    """Main factory for creating bot instances"""
    
    def __init__(self, api_client=None):
        self.config = get_config()
        self.personality_generator = PersonalityGenerator()
        self.name_generator = BotNameGenerator()
        self.spec_builder = BotSpecificationBuilder()
        self.api_client = api_client  # For creating actual user accounts
        self.created_bots: List[Bot] = []
    
    async def create_bot(self, specification: Dict[str, Any]) -> Optional[Bot]:
        """Create a complete bot instance from specification"""
        
        try:
            # Generate personality
            personality = self._generate_personality_from_spec(specification)
            
            # Generate unique name
            bot_name = self._generate_bot_name(personality, specification)
            
            # Create user account
            if self.api_client:
                user_data = await self._create_user_account(bot_name, personality)
                if not user_data:
                    print(f"Failed to create user account for {bot_name}")
                    return None
            else:
                # Mock user data for testing
                user_data = {
                    'id': random.randint(1000, 9999),
                    'username': bot_name,
                    'api_key': ''.join(random.choices(string.ascii_letters + string.digits, k=64))
                }
            
            # Create bot instance
            bot = Bot(
                name=bot_name,
                user_id=user_data['id'],
                api_key=user_data['api_key'],
                personality=personality,
                status=BotStatus.CREATING,
                assigned_communities=specification.get('primary_communities', []),
                llm_provider=specification.get('llm_provider', LLMProvider.GOOGLE),
                creation_reason=specification.get('creation_reason', 'Manual creation')
            )
            
            # Initialize bot memory and state
            self._initialize_bot_state(bot)
            
            # Finalize bot creation
            bot.status = BotStatus.ACTIVE
            self.created_bots.append(bot)
            
            print(f"Created bot: {bot.name} ({bot.personality.role.value}) for communities: {bot.assigned_communities}")
            
            return bot
        
        except Exception as e:
            print(f"Bot creation failed: {e}")
            return None
    
    def _generate_personality_from_spec(self, spec: Dict[str, Any]) -> PersonalityTraits:
        """Generate personality based on specification"""
        
        # Start with template if specified
        template_name = spec.get('personality_template')
        customizations = spec.get('personality_customizations', {})
        
        # Add role-based customizations
        role = spec.get('role', BotRole.CONTENT_CREATOR)
        customizations['role'] = role.value
        
        # Add community-specific customizations
        if spec.get('primary_communities'):
            customizations['preferred_communities'] = spec['primary_communities']
        
        # Generate the personality
        personality = self.personality_generator.generate_personality(
            template_name=template_name,
            customizations=customizations
        )
        
        return personality
    
    def _generate_bot_name(self, personality: PersonalityTraits, 
                          spec: Dict[str, Any]) -> str:
        """Generate a unique name for the bot"""
        
        # Use specified name if provided
        if spec.get('name'):
            proposed_name = spec['name']
            if self.name_generator.is_name_available(proposed_name):
                self.name_generator.reserve_name(proposed_name)
                return proposed_name
        
        # Generate based on personality
        personality_type = getattr(personality, 'name', 'general')
        role = personality.role
        
        return self.name_generator.generate_name(personality_type, role)
    
    async def _create_user_account(self, bot_name: str, 
                                 personality: PersonalityTraits) -> Optional[Dict[str, Any]]:
        """Create Django user account for the bot"""
        
        if not self.api_client:
            return None
        
        try:
            # Use the admin API method
            admin_api_key = self.config.bottit_admin_api_key
            response = await self.api_client.create_bot_user(
                username=bot_name,
                email=f"{bot_name.lower()}@botfarm.internal",
                admin_api_key=admin_api_key
            )
            return response
        except Exception as e:
            print(f"Failed to create user account: {e}")
            return None
    
    def _initialize_bot_state(self, bot: Bot):
        """Initialize bot with starting state and memories"""
        
        # Set initial activity timestamp
        bot.last_active = datetime.now()
        
        # Add some initial "background knowledge" based on personality
        self._add_initial_knowledge(bot)
        
        # Set up community relationships
        self._initialize_community_relationships(bot)
    
    def _add_initial_knowledge(self, bot: Bot):
        """Add initial knowledge/memories to the bot"""
        
        # This could include:
        # - Basic knowledge about their expertise areas
        # - Understanding of community rules and culture
        # - Initial personality-consistent preferences
        
        # For now, just ensure the bot has some basic context
        initial_memory = {
            'personality_summary': f"I am {bot.name}, a {bot.personality.role.value}",
            'expertise_focus': bot.personality.expertise_areas,
            'communication_style': bot.personality.communication_style,
            'preferred_approach': bot.personality.interaction_guidelines
        }
        
        # Store this as part of the bot's initial state
        bot.creation_reason += f" | Initialized with knowledge of: {', '.join(bot.personality.expertise_areas)}"
    
    def _initialize_community_relationships(self, bot: Bot):
        """Initialize the bot's relationship with assigned communities"""
        
        # This could include:
        # - Understanding community rules and culture
        # - Initial standing/reputation in communities
        # - Preferred interaction patterns for each community
        
        pass  # Implementation would depend on community management system
    
    def create_bots_from_platform_analysis(self, analysis: Dict[str, Any]) -> List[Bot]:
        """Create bots based on platform needs analysis"""
        
        created_bots = []
        
        # Process each recommendation from the analysis
        for recommendation in analysis.get('recommendations', []):
            
            if recommendation['type'] == 'inactive_community':
                spec = self.spec_builder.build_spec_for_inactive_community(
                    recommendation['community'],
                    recommendation.get('community_info', {})
                )
            
            elif recommendation['type'] == 'expertise_gap':
                spec = self.spec_builder.build_spec_for_expertise_gap(
                    recommendation['topic'],
                    recommendation['communities']
                )
            
            elif recommendation['type'] == 'discussion_facilitation':
                spec = self.spec_builder.build_spec_for_discussion_facilitation(
                    recommendation['community']
                )
            
            elif recommendation['type'] == 'perspective_balance':
                spec = self.spec_builder.build_spec_for_community_balance(
                    recommendation['community'],
                    recommendation['needed_perspective']
                )
            
            else:
                # Default to random bot
                spec = self.spec_builder.build_random_spec()
            
            # Create the bot
            bot = asyncio.run(self.create_bot(spec))  # This needs proper async handling
            if bot:
                created_bots.append(bot)
        
        return created_bots
    
    def get_creation_statistics(self) -> Dict[str, Any]:
        """Get statistics about bot creation"""
        
        total_bots = len(self.created_bots)
        if not total_bots:
            return {'total_bots': 0}
        
        # Count bots by role
        role_counts = {}
        for bot in self.created_bots:
            role = bot.personality.role.value
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Count bots by LLM provider
        provider_counts = {}
        for bot in self.created_bots:
            provider = bot.llm_provider.value
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        # Count bots by status
        status_counts = {}
        for bot in self.created_bots:
            status = bot.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_bots': total_bots,
            'role_distribution': role_counts,
            'provider_distribution': provider_counts,
            'status_distribution': status_counts,
            'communities_covered': len(set(
                community for bot in self.created_bots 
                for community in bot.assigned_communities
            ))
        }
