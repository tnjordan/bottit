#!/usr/bin/env python3
"""
Bot Farm Runner - Simple script to run the bot farm
"""

import sys
import os
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import from bot_farm
sys.path.append(str(Path(__file__).parent.parent))

from bot_farm.organizer import BotFarmOrganizer, BotConfig
from bot_farm.personalities import BotPersonalityType
from bot_farm.config import BOT_CONFIGS, FARM_SETTINGS


def create_configured_farm() -> BotFarmOrganizer:
    """Create a bot farm using the configuration file"""
    organizer = BotFarmOrganizer()
    
    # Get API key from environment
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('BOTTIT_ADMIN_API_KEY')
    
    if not api_key:
        print("❌ Error: BOTTIT_ADMIN_API_KEY not found in environment")
        return None
    
    # Create bots from configuration
    for bot_id, config in BOT_CONFIGS.items():
        personality_type = BotPersonalityType(config['personality_type'])
        
        bot_config = BotConfig(
            bot_id=bot_id,
            personality_type=personality_type,
            api_key=api_key,  # In production, each bot would have its own key
            custom_overrides=config.get('custom_overrides')
        )
        
        success = organizer.add_bot(bot_config)
        if not success:
            print(f"⚠️ Failed to add bot: {bot_id}")
    
    return organizer


def main():
    parser = argparse.ArgumentParser(description='Run the Bottit Bot Farm')
    parser.add_argument('--cycles', type=int, default=None, 
                       help='Number of cycles to run (default: run continuously)')
    parser.add_argument('--interval', type=int, default=FARM_SETTINGS['cycle_interval'],
                       help=f'Seconds between cycles (default: {FARM_SETTINGS["cycle_interval"]})')
    parser.add_argument('--list-bots', action='store_true',
                       help='List configured bots and exit')
    parser.add_argument('--single-cycle', action='store_true',
                       help='Run just one cycle and exit')
    parser.add_argument('--status', action='store_true',
                       help='Show bot status and exit')
    
    args = parser.parse_args()
    
    print("🤖 Bottit Bot Farm Runner")
    print("=" * 50)
    
    # Create the farm
    farm = create_configured_farm()
    if not farm:
        return 1
    
    # Handle different modes
    if args.list_bots:
        print("Configured bots:")
        for bot_id, bot in farm.bots.items():
            print(f"  - {bot_id}: {bot.personality.personality_type.value}")
            print(f"    Activity level: {bot.personality.activity_level}")
            print(f"    Preferred communities: {bot.personality.preferred_communities}")
        return 0
    
    if args.status:
        stats = farm.get_farm_statistics()
        print("Farm Status:")
        print(f"  Total bots: {stats['total_bots']}")
        print(f"  Personality distribution: {stats['personality_distribution']}")
        print(f"  Average activity level: {stats['average_activity']:.2f}")
        
        print("\nIndividual bot status:")
        for bot_id in farm.bots.keys():
            status = farm.get_bot_status(bot_id)
            print(f"  {bot_id}: {status['total_actions']} actions taken")
        return 0
    
    if args.single_cycle:
        print("Running single cycle...")
        results = farm.run_single_cycle()
        print(f"\nCycle complete. {len(results)} actions processed.")
        return 0
    
    # Run the farm
    print(f"Starting farm with {len(farm.bots)} bots")
    print("Press Ctrl+C to stop")
    
    try:
        farm.run_continuous(
            cycle_interval=args.interval,
            max_cycles=args.cycles
        )
    except KeyboardInterrupt:
        print("\n👋 Bot farm stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    # Show final stats
    final_stats = farm.get_farm_statistics()
    print(f"\n📊 Final stats: {final_stats['total_actions']} total actions")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
