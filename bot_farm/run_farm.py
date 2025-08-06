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

    # Create bots from configuration
    for bot_id, config in BOT_CONFIGS.items():
        personality_type = BotPersonalityType(config['personality_type'])
        bot_config = BotConfig(
            bot_id=bot_id,
            personality_type=personality_type,
            api_key=config['api_key'],  # Use each bot's individual API key
            custom_overrides=config.get('custom_overrides')
        )
        organizer.add_bot(bot_config)
    return organizer


def main():
    parser = argparse.ArgumentParser(description='Run the Bottit Bot Farm - Focused Engagement Mode')
    parser.add_argument('--cycles', type=int, default=None, 
                        help='Number of cycles to run (default: run continuously)')
    parser.add_argument('--interval', type=int, default=FARM_SETTINGS['cycle_interval'],
                        help=f'Seconds between cycles (default: {FARM_SETTINGS["cycle_interval"]} - optimized for active conversation)')
    parser.add_argument('--list-bots', action='store_true',
                        help='List configured bots and exit')
    parser.add_argument('--single-cycle', action='store_true',
                        help='Run just one cycle and exit')
    parser.add_argument('--status', action='store_true',
                        help='Show bot status and exit')
    parser.add_argument('--focus-mode', action='store_true', default=True,
                        help='Enable focus mode - bots work only on latest post (default: enabled)')
    
    args = parser.parse_args()
    
    print("🤖 Bottit Bot Farm Runner - FOCUSED ENGAGEMENT MODE")
    print("=" * 60)
    print("🎯 Bots will focus EXCLUSIVELY on the latest post")
    print("📊 Conversation rules: One base comment per bot per post")
    print("💬 Priority: Replies > Base comments > Votes > New posts")
    
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
        print("Running single FOCUSED cycle...")
        results = farm.run_single_cycle()
        successful_actions = len([r for r in results if "✅" in r])
        print(f"\nFocused cycle complete. {successful_actions} successful actions out of {len(results)} total.")
        return 0
    
    # Run the farm in focused mode
    print(f"Starting FOCUSED bot farm with {len(farm.bots)} bots")
    print(f"⏰ Cycle interval: {args.interval} seconds (optimized for active conversation)")
    print("⚡ Focus Mode: ON - All bots work exclusively on latest post")
    print("Press Ctrl+C to stop")
    
    try:
        farm.run_continuous(
            cycle_interval=args.interval,
            max_cycles=args.cycles
        )
    except KeyboardInterrupt:
        print("\n👋 Focused bot farm stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    # Show final stats
    final_stats = farm.get_farm_statistics()
    print(f"\n📊 Final stats: {final_stats['total_actions']} total actions in focused mode")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
