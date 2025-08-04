#!/usr/bin/env python3
"""
Quick test of a single bot with existing credentials
"""

import sys
import os
from pathlib import Path
import json

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from bot_farm.personalities import BotPersonalityType
from bot_farm.organizer import BotFarmOrganizer, BotConfig
from dotenv import load_dotenv

load_dotenv()


def test_single_bot():
    """Test a single bot interaction"""
    print("🧪 Testing single bot interaction...")
    
    # Check environment
    api_url = os.getenv('BOTTIT_API_URL')
    if not api_url:
        print("❌ No BOTTIT_API_URL found")
        return
    
    # Load bot credentials
    credentials_file = Path(__file__).parent / "bot_farm" / "bot_credentials.json"
    if not credentials_file.exists():
        print("❌ No bot credentials found")
        return
    
    with open(credentials_file, 'r') as f:
        bot_credentials = json.load(f)
    
    # Pick one bot to test
    test_bot_id = "alice_enthusiast"
    if test_bot_id not in bot_credentials:
        print(f"❌ No credentials for {test_bot_id}")
        print(f"Available bots: {list(bot_credentials.keys())}")
        return
    
    print(f"🤖 Testing bot: {test_bot_id}")
    print(f"🔗 API URL: {api_url}")
    
    # Create organizer
    farm = BotFarmOrganizer(base_url=api_url)
    
    # Add the test bot
    config = BotConfig(
        bot_id=test_bot_id,
        personality_type=BotPersonalityType.ENTHUSIAST,
        api_key=bot_credentials[test_bot_id]['api_key']
    )
    
    if not farm.add_bot(config):
        print("❌ Failed to add bot")
        return
    
    print("✅ Bot added successfully")
    
    # Run a single cycle
    print("\n🔄 Running single bot cycle...")
    results = farm.run_single_cycle()
    
    print("\n📊 Results:")
    for result in results:
        print(f"  {result}")


if __name__ == '__main__':
    test_single_bot()
