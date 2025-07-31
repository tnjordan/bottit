#!/usr/bin/env python3
"""
Simple test to verify Google/Gemini configuration is working
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import bot_farm modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

print("🔧 Testing Google/Gemini Configuration")
print("=" * 40)

try:
    from bot_farm.config import get_config, LLMProvider
    print("✅ Successfully imported configuration modules")
    
    config = get_config()
    print(f"✅ Default LLM Provider: {config.default_llm_provider.value}")
    
    google_config = config.llm_providers.get(LLMProvider.GOOGLE)
    if google_config:
        api_key = google_config.get('api_key')
        print(f"✅ Google configuration found")
        print(f"   Model: {google_config.get('model')}")
        if api_key:
            print(f"   API Key: ****{api_key[-4:]}")
        else:
            print("❌ No GEMINI_API_KEY found in environment")
    else:
        print("❌ No Google configuration found")
    
    print(f"✅ Available LLM providers: {list(config.llm_providers.keys())}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

try:
    import google.generativeai as genai
    print("✅ Google Generative AI library available")
except ImportError:
    print("❌ Google Generative AI library not installed")
    print("   Run: pip install google-generativeai")
    sys.exit(1)

print("\n🎉 Configuration test completed!")
print("\nNext: Run the bot farm with:")
print("   python -m bot_farm start --max-bots 5")
