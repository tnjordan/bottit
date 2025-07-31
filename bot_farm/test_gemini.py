#!/usr/bin/env python3
"""
Test script for Gemini integration with the bot farm system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the bot_farm directory to Python path
bot_farm_dir = Path(__file__).parent
sys.path.insert(0, str(bot_farm_dir))

try:
    from bot_farm.config import get_config, LLMProvider
    from bot_farm.response_engine import LLMClient
    from bot_farm.personalities import PersonalityGenerator, PersonalityPromptBuilder
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the bot_farm directory")
    sys.exit(1)


async def test_gemini_integration():
    """Test the Gemini integration"""
    
    print("🧪 Testing Gemini Integration for Bot Farm")
    print("=" * 50)
    
    # Test configuration
    print("1. Testing configuration...")
    config = get_config()
    
    if config.default_llm_provider != LLMProvider.GOOGLE:
        print(f"❌ Default LLM provider is {config.default_llm_provider.value}, should be google")
        return False
    
    google_config = config.llm_providers.get(LLMProvider.GOOGLE)
    if not google_config:
        print("❌ No Google configuration found")
        return False
    
    if not google_config.get('api_key'):
        print("❌ No GEMINI_API_KEY found in environment")
        print("   Make sure you have GEMINI_API_KEY in your .env file")
        return False
    
    print(f"✅ Configuration loaded:")
    print(f"   Model: {google_config.get('model')}")
    print(f"   API Key: {'***' + google_config.get('api_key')[-4:] if google_config.get('api_key') else 'Not found'}")
    
    # Test LLM client initialization
    print("\n2. Testing LLM client initialization...")
    try:
        client = LLMClient(LLMProvider.GOOGLE)
        print("✅ LLM client created successfully")
    except Exception as e:
        print(f"❌ Failed to create LLM client: {e}")
        return False
    
    # Test basic response generation
    print("\n3. Testing basic response generation...")
    try:
        system_prompt = "You are a helpful assistant. Respond briefly and clearly."
        user_prompt = "What is the opposite of hot?"
        
        response = await client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"✅ Response generated successfully:")
        print(f"   Prompt: {user_prompt}")
        print(f"   Response: {response}")
        
        if len(response.strip()) == 0:
            print("❌ Response is empty")
            return False
            
    except Exception as e:
        print(f"❌ Failed to generate response: {e}")
        return False
    
    # Test with bot personality
    print("\n4. Testing with bot personality...")
    try:
        generator = PersonalityGenerator()
        personality = generator.generate_personality('tech_expert')
        prompt_builder = PersonalityPromptBuilder(personality)
        
        bot_system_prompt = prompt_builder.build_system_prompt()
        bot_user_prompt = "What do you think about Python programming?"
        
        bot_response = await client.generate_response(
            system_prompt=bot_system_prompt,
            user_prompt=bot_user_prompt,
            temperature=0.8,
            max_tokens=200
        )
        
        print(f"✅ Bot personality response generated:")
        print(f"   Personality: {personality.role.value}")
        print(f"   Response: {bot_response[:200]}...")
        
    except Exception as e:
        print(f"❌ Failed to generate bot personality response: {e}")
        return False
    
    print("\n🎉 All tests passed! Gemini integration is working correctly.")
    return True


async def test_multiple_responses():
    """Test generating multiple different responses"""
    
    print("\n5. Testing multiple responses for variety...")
    
    client = LLMClient(LLMProvider.GOOGLE)
    
    prompts = [
        "What's your favorite programming language?",
        "How do you feel about artificial intelligence?",
        "What makes a good software developer?",
    ]
    
    for i, prompt in enumerate(prompts, 1):
        try:
            response = await client.generate_response(
                system_prompt="You are a tech expert bot. Be friendly and informative.",
                user_prompt=prompt,
                temperature=0.8,
                max_tokens=150
            )
            print(f"   {i}. Q: {prompt}")
            print(f"      A: {response[:100]}...")
            
        except Exception as e:
            print(f"❌ Failed on prompt {i}: {e}")
            return False
    
    print("✅ Multiple responses generated successfully")
    return True


def main():
    """Main test function"""
    
    print("Starting Gemini integration test...")
    
    try:
        # Run basic tests
        success = asyncio.run(test_gemini_integration())
        
        if success:
            # Run additional tests
            asyncio.run(test_multiple_responses())
            print("\n🚀 Gemini integration is ready for the bot farm!")
            print("\nNext steps:")
            print("1. Run: python -m bot_farm start --max-bots 5")
            print("2. Check status: python -m bot_farm status")
            print("3. Create a bot: python -m bot_farm create-bot --role expert")
        else:
            print("\n❌ Integration test failed. Please check the errors above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
