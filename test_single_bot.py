#!/usr/bin/env python3
"""
Simple test to get a single bot to call the Gemini LLM
"""

import asyncio
from bot_farm.models import Bot, BotRole, InteractionType, PersonalityTraits
from bot_farm.response_engine import ResponseEngine
from bot_farm.config import LLMProvider


async def test_single_bot_llm_call():
    """Test a single bot calling the Gemini LLM"""
    
    print("🤖 Testing single bot LLM call...")
    
    # Create a simple bot
    bot = Bot(
        bot_id="test_bot",
        username="TestBot",
        display_name="Test Bot",
        role=BotRole.CONTENT_CREATOR,
        personality=PersonalityTraits(
            name="Test Bot",
            role=BotRole.CONTENT_CREATOR,
            communication_style="casual and friendly",
            expertise_areas=["technology", "programming"],
            emotional_tone="helpful and positive"
        ),
        llm_provider=LLMProvider.GOOGLE
    )
    
    print(f"✅ Created bot: {bot.username}")
    
    # Create response engine
    response_engine = ResponseEngine()
    print("✅ Created response engine")
    
    # Create test context for a post
    context = {
        'prompt': "Write a thoughtful post about the benefits of open source software"
    }
    
    print("🚀 Calling Gemini LLM...")
    
    try:
        response = await response_engine.generate_response(
            bot=bot,
            context=context,
            interaction_type=InteractionType.POST
        )
        
        if response:
            print("✅ SUCCESS! LLM response received:")
            print(f"🔥 Response: {response}")
        else:
            print("❌ No response received from LLM")
            
    except Exception as e:
        print(f"❌ Error calling LLM: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_bot_llm_call())
