#!/usr/bin/env python3
"""
Test bot behavior with real API calls (requires Django server running)
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append('/home/todd/gt/bottit')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bottit.settings')
django.setup()

from bot_farm.organizer import BotFarmOrganizer, BotConfig
from bot_farm.personalities import BotPersonalityType
from core.models import CustomUser


def test_real_bot_interaction():
    """Test bot behavior with actual API calls"""
    print("🔧 Testing real bot interactions...")
    
    # Create a real bot user in the database
    bot_user, created = CustomUser.objects.get_or_create(
        username='test_interaction_bot',
        defaults={
            'email': 'test_interaction_bot@example.com',
            'is_bot': True
        }
    )
    
    if created:
        print(f"✅ Created bot user: {bot_user.username}")
    else:
        print(f"✅ Using existing bot user: {bot_user.username}")
    
    # Set up organizer - this will try to make real API calls
    organizer = BotFarmOrganizer(base_url="http://localhost:8000/api")
    
    # Add bot with real configuration
    test_config = BotConfig(
        bot_id=bot_user.username,
        personality_type=BotPersonalityType.CASUAL,
        api_key="dummy_key"  # Won't work for authenticated endpoints
    )
    
    if organizer.add_bot(test_config):
        print("✅ Bot added to organizer")
    else:
        print("❌ Failed to add bot")
        return
    
    # Test a single cycle
    print("\n🔄 Running single bot cycle...")
    try:
        results = organizer.run_single_cycle()
        print("\n📊 Results:")
        for result in results:
            print(f"  {result}")
    except Exception as e:
        print(f"❌ Error running cycle: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("⚠️  This test requires the Django server to be running on localhost:8000")
    print("⚠️  Start it with: .venv/bin/python manage.py runserver 8000")
    print()
    
    test_real_bot_interaction()
