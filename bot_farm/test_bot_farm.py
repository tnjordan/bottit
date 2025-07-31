"""
Bot Farm Tests

Basic test suite for the bot farm system
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from bot_farm.models import Bot, BotPersonality, BotRole, BotInteraction
from bot_farm.personalities import PersonalityGenerator, PersonalityPromptBuilder
from bot_farm.memory_system import BotMemoryStorage, BotMemoryManager
from bot_farm.response_engine import ResponseQualityScorer, RepetitionPreventer
from bot_farm.coordination import OrganicTimingEngine, BotCoordinator
from bot_farm.bot_factory import BotNameGenerator, BotFactory
from bot_farm.config import BotFarmConfig, get_config


class TestPersonalitySystem:
    """Test bot personality generation and management"""
    
    def test_personality_generator(self):
        """Test personality generation"""
        generator = PersonalityGenerator()
        
        # Test getting available templates
        templates = generator.get_available_templates()
        assert len(templates) > 0
        assert 'tech_expert' in templates
        
        # Test generating personality
        personality = generator.generate_personality('tech_expert')
        assert personality is not None
        assert personality.role == BotRole.EXPERT
        assert len(personality.interests) > 0
    
    def test_personality_prompt_builder(self):
        """Test personality prompt building"""
        generator = PersonalityGenerator()
        personality = generator.generate_personality('tech_expert')
        
        builder = PersonalityPromptBuilder(personality)
        prompt = builder.build_system_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        assert personality.role.value in prompt.lower()


class TestMemorySystem:
    """Test bot memory storage and management"""
    
    @pytest.fixture
    async def memory_storage(self):
        """Create test memory storage"""
        storage = BotMemoryStorage(':memory:')  # In-memory SQLite
        await storage.initialize()
        yield storage
        await storage.close()
    
    @pytest.mark.asyncio
    async def test_memory_storage(self, memory_storage):
        """Test basic memory operations"""
        bot_id = 'test_bot_1'
        
        # Store memory
        await memory_storage.store_memory(bot_id, 'interaction', {
            'content': 'Test interaction',
            'timestamp': datetime.now().isoformat()
        })
        
        # Retrieve memory
        memories = await memory_storage.get_memories(bot_id, 'interaction', limit=10)
        assert len(memories) == 1
        assert memories[0]['content'] == 'Test interaction'
    
    @pytest.mark.asyncio
    async def test_memory_manager(self, memory_storage):
        """Test memory manager functionality"""
        generator = PersonalityGenerator()
        personality = generator.generate_personality('casual_user')
        
        manager = BotMemoryManager(memory_storage, personality)
        
        # Create test interaction
        interaction = BotInteraction(
            bot_id='test_bot',
            interaction_type='comment',
            target_id='post_123',
            content='This is a test comment',
            timestamp=datetime.now(),
            success=True
        )
        
        # Learn from interaction
        await manager.learn_from_interaction(interaction)
        
        # Get relevant context
        context = await manager.get_relevant_context('programming', limit=5)
        assert isinstance(context, str)


class TestResponseEngine:
    """Test response generation and quality control"""
    
    def test_quality_scorer(self):
        """Test response quality scoring"""
        scorer = ResponseQualityScorer()
        
        # Test good response
        good_response = "This is a thoughtful and well-structured response that adds value to the discussion."
        good_score = scorer.score_response(good_response, 'general')
        assert good_score > 0.5
        
        # Test poor response
        poor_response = "ok"
        poor_score = scorer.score_response(poor_response, 'general')
        assert poor_score < 0.5
    
    def test_repetition_preventer(self):
        """Test repetition prevention"""
        preventer = RepetitionPreventer()
        
        # Add some responses
        preventer.add_response('bot1', 'This is a test response')
        preventer.add_response('bot1', 'This is another response')
        preventer.add_response('bot2', 'This is a test response')  # Same content, different bot
        
        # Test similarity detection
        similar = preventer.is_too_similar('bot1', 'This is a test response')
        assert similar  # Should detect repetition
        
        different = preventer.is_too_similar('bot1', 'This is completely different content')
        assert not different  # Should not detect repetition


class TestCoordination:
    """Test bot coordination and timing"""
    
    def test_organic_timing(self):
        """Test organic timing generation"""
        engine = OrganicTimingEngine()
        
        # Test delay generation
        delay = engine.get_next_action_delay()
        assert delay > 0
        assert delay < 3600  # Should be reasonable (< 1 hour)
        
        # Test response delay
        response_delay = engine.get_response_delay('comment')
        assert response_delay > 0
    
    @pytest.mark.asyncio
    async def test_bot_coordinator(self):
        """Test bot coordination"""
        coordinator = BotCoordinator()
        
        # Mock some bots
        bot1 = Mock()
        bot1.id = 'bot1'
        bot1.status = 'active'
        bot1.last_activity = datetime.now() - timedelta(minutes=30)
        
        bot2 = Mock()
        bot2.id = 'bot2'
        bot2.status = 'active'
        bot2.last_activity = datetime.now() - timedelta(minutes=5)
        
        coordinator.register_bot(bot1)
        coordinator.register_bot(bot2)
        
        # Test activity scheduling
        next_bot = await coordinator.get_next_active_bot()
        assert next_bot is not None


class TestBotFactory:
    """Test bot creation and management"""
    
    def test_name_generator(self):
        """Test bot name generation"""
        generator = BotNameGenerator()
        
        # Test tech expert names
        tech_names = [generator.generate_name(BotRole.EXPERT) for _ in range(10)]
        assert len(set(tech_names)) == 10  # Should be unique
        
        # Test casual user names
        casual_names = [generator.generate_name(BotRole.CONTENT_CREATOR) for _ in range(10)]
        assert len(set(casual_names)) == 10  # Should be unique
    
    @pytest.mark.asyncio
    async def test_bot_factory(self):
        """Test bot factory creation"""
        # Mock API client
        api_client = AsyncMock()
        api_client.create_bot_account.return_value = {
            'id': 123,
            'username': 'test_bot',
            'api_key': 'test_api_key'
        }
        
        factory = BotFactory(api_client)
        
        # Test bot creation
        spec = {
            'creation_reason': 'Test creation',
            'personality_template': 'tech_expert',
            'primary_communities': ['programming'],
            'priority': 5
        }
        
        bot = await factory.create_bot(spec)
        assert bot is not None
        assert bot.name == 'test_bot'
        assert bot.api_key == 'test_api_key'


class TestConfiguration:
    """Test configuration management"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = get_config()
        
        assert isinstance(config, BotFarmConfig)
        assert config.max_managed_bots > 0
        assert config.god_bot_check_interval > 0
        assert config.bottit_api_url is not None
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test invalid config
        with pytest.raises(ValueError):
            BotFarmConfig(
                max_managed_bots=-1,  # Invalid
                god_bot_check_interval=60
            )


class TestModels:
    """Test data models"""
    
    def test_bot_model(self):
        """Test Bot model"""
        personality = BotPersonality(
            role=BotRole.EXPERT,
            interests=['programming', 'AI'],
            style_traits={'technical': 0.8, 'friendly': 0.6},
            response_patterns=['analytical', 'helpful']
        )
        
        bot = Bot(
            id='test_bot',
            name='TestBot',
            personality=personality,
            api_key='test_key',
            assigned_communities=['programming'],
            status='active',
            created_at=datetime.now()
        )
        
        assert bot.id == 'test_bot'
        assert bot.personality.role == BotRole.EXPERT
        assert 'programming' in bot.assigned_communities
    
    def test_bot_interaction(self):
        """Test BotInteraction model"""
        interaction = BotInteraction(
            bot_id='test_bot',
            interaction_type='comment',
            target_id='post_123',
            content='Test comment',
            timestamp=datetime.now(),
            success=True
        )
        
        assert interaction.bot_id == 'test_bot'
        assert interaction.success is True


# Test fixtures and utilities

@pytest.fixture
def sample_bot():
    """Create a sample bot for testing"""
    personality = BotPersonality(
        role=BotRole.CONTENT_CREATOR,
        interests=['general', 'discussion'],
        style_traits={'casual': 0.7, 'engaging': 0.8},
        response_patterns=['conversational', 'supportive']
    )
    
    return Bot(
        id='sample_bot',
        name='SampleBot',
        personality=personality,
        api_key='sample_key',
        assigned_communities=['general'],
        status='active',
        created_at=datetime.now()
    )


@pytest.fixture
def mock_api_client():
    """Create a mock API client"""
    client = AsyncMock()
    client.health_check.return_value = True
    client.get_communities.return_value = [
        {'name': 'programming', 'member_count': 1000},
        {'name': 'general', 'member_count': 500}
    ]
    client.get_posts.return_value = []
    client.create_post.return_value = {'id': 123}
    client.create_comment.return_value = {'id': 456}
    return client


# Integration test helpers

async def run_integration_test():
    """Run basic integration test"""
    print("🧪 Running integration test...")
    
    try:
        from bot_farm.runner import BotFarmRunner
        
        # Test configuration
        runner = BotFarmRunner({
            'max_managed_bots': 2,
            'god_bot_check_interval': 10
        })
        
        # This would test the full system startup
        # For now, just test configuration
        assert runner.config.max_managed_bots == 2
        
        print("✅ Integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


if __name__ == '__main__':
    # Run basic integration test
    asyncio.run(run_integration_test())
