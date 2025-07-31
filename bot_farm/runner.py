"""
Bot Farm Runner

Main entry point and utilities for running the bot farm system
"""

import asyncio
import signal
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

from .god_bot import GodBot
from .api_client import BottitAPIClient
from .config import get_config, update_config


class BotFarmRunner:
    """Main runner for the bot farm system"""
    
    def __init__(self, config_overrides: Optional[Dict[str, Any]] = None):
        # Update configuration if overrides provided
        if config_overrides:
            update_config(**config_overrides)
        
        self.config = get_config()
        self.god_bot: Optional[GodBot] = None
        self.api_client: Optional[BottitAPIClient] = None
        self.is_running = False
    
    async def start(self):
        """Start the bot farm system"""
        
        print("🚀 Starting Bot Farm System...")
        print(f"📋 Configuration: {self.config.max_managed_bots} max bots, "
              f"{self.config.god_bot_check_interval}s check interval")
        
        try:
            # Initialize API client
            self.api_client = BottitAPIClient()
            
            # Test API connection
            if not await self.api_client.health_check():
                print("❌ Cannot connect to bottit API. Please check configuration.")
                return False
            
            print("✅ Connected to bottit API")
            
            # Initialize God Bot
            self.god_bot = GodBot(self.api_client)
            
            # Set up signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Start the God Bot
            await self.god_bot.start()
            
            self.is_running = True
            print("🤖 Bot Farm System is now running!")
            
            # Keep the system running
            while self.is_running:
                await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Bot Farm System: {e}")
            return False
        
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the bot farm system"""
        
        print("🛑 Stopping Bot Farm System...")
        
        self.is_running = False
        
        if self.god_bot:
            await self.god_bot.stop()
        
        if self.api_client:
            await self.api_client.close()
        
        print("✅ Bot Farm System stopped")
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        
        def signal_handler(signum, frame):
            print(f"\n📡 Received signal {signum}, initiating graceful shutdown...")
            self.is_running = False
        
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Kill command
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        
        status = {
            'is_running': self.is_running,
            'start_time': datetime.now().isoformat(),
            'configuration': {
                'max_bots': self.config.max_managed_bots,
                'check_interval': self.config.god_bot_check_interval,
                'default_llm': self.config.default_llm_provider.value
            }
        }
        
        if self.god_bot:
            status['god_bot'] = self.god_bot.get_status()
        
        return status


class BotFarmCLI:
    """Command line interface for bot farm operations"""
    
    def __init__(self):
        self.runner = BotFarmRunner()
    
    async def run_command(self, command: str, args: Dict[str, Any] = None):
        """Run a CLI command"""
        
        if command == 'start':
            await self._start_command(args or {})
        elif command == 'status':
            await self._status_command()
        elif command == 'create-bot':
            await self._create_bot_command(args or {})
        elif command == 'list-bots':
            await self._list_bots_command()
        elif command == 'test-api':
            await self._test_api_command()
        else:
            print(f"❌ Unknown command: {command}")
            self._print_help()
    
    async def _start_command(self, args: Dict[str, Any]):
        """Start the bot farm system"""
        
        # Apply any configuration overrides from command line
        config_overrides = {}
        
        if args.get('max_bots'):
            config_overrides['max_managed_bots'] = int(args['max_bots'])
        
        if args.get('check_interval'):
            config_overrides['god_bot_check_interval'] = int(args['check_interval'])
        
        if args.get('api_url'):
            config_overrides['bottit_api_url'] = args['api_url']
        
        # Create runner with overrides
        if config_overrides:
            self.runner = BotFarmRunner(config_overrides)
        
        # Start the system
        success = await self.runner.start()
        
        if not success:
            sys.exit(1)
    
    async def _status_command(self):
        """Show system status"""
        
        if not self.runner.god_bot:
            print("❌ Bot Farm System is not running")
            return
        
        status = self.runner.get_status()
        
        print("📊 Bot Farm System Status:")
        print(f"   Running: {status['is_running']}")
        
        if status.get('god_bot'):
            god_status = status['god_bot']
            print(f"   Active Bots: {god_status['active_bots_count']}/{god_status['managed_bots_count']}")
            print(f"   Created Today: {god_status['bots_created_today']}")
            print(f"   Retired Today: {god_status['bots_retired_today']}")
            print(f"   Ecosystem Health: {god_status['ecosystem_health_score']:.2f}")
    
    async def _create_bot_command(self, args: Dict[str, Any]):
        """Manually create a bot"""
        
        if not self.runner.god_bot:
            print("❌ Bot Farm System is not running")
            return
        
        # Build bot specification from args
        spec = {
            'creation_reason': args.get('reason', 'Manual CLI creation'),
            'role': args.get('role', 'content_creator'),
            'primary_communities': args.get('communities', '').split(',') if args.get('communities') else [],
            'personality_template': args.get('template'),
            'priority': int(args.get('priority', 5))
        }
        
        # Create the bot
        bot = await self.runner.god_bot.create_bot_manually(spec)
        
        if bot:
            print(f"✅ Created bot: {bot.name} ({bot.personality.role.value})")
            print(f"   Communities: {', '.join(bot.assigned_communities)}")
        else:
            print("❌ Failed to create bot")
    
    async def _list_bots_command(self):
        """List all managed bots"""
        
        if not self.runner.god_bot:
            print("❌ Bot Farm System is not running")
            return
        
        bots = self.runner.god_bot.get_bot_roster()
        
        if not bots:
            print("📝 No bots currently managed")
            return
        
        print(f"🤖 Managed Bots ({len(bots)}):")
        
        for bot in bots:
            status_emoji = {
                'active': '🟢',
                'inactive': '🟡',
                'creating': '🔄',
                'optimizing': '🔧',
                'retired': '⚫'
            }.get(bot['status'], '❓')
            
            print(f"   {status_emoji} {bot['name']} ({bot['role']})")
            print(f"      Communities: {', '.join(bot['communities'])}")
            print(f"      Performance: {bot['performance_score']:.2f}")
            print(f"      Created: {bot['created_at']}")
            print()
    
    async def _test_api_command(self):
        """Test API connection"""
        
        print("🔍 Testing API connection...")
        
        async with BottitAPIClient() as client:
            if await client.health_check():
                print("✅ API connection successful")
                
                # Test getting communities
                communities = await client.get_communities()
                if communities:
                    print(f"📂 Found {len(communities)} communities:")
                    for community in communities[:5]:  # Show first 5
                        print(f"   - c/{community['name']}: {community['member_count']} members")
                else:
                    print("❌ Could not retrieve communities")
            else:
                print("❌ API connection failed")
    
    def _print_help(self):
        """Print CLI help"""
        
        print("""
🤖 Bot Farm CLI Commands:

start                    - Start the bot farm system
  --max-bots N          - Maximum number of bots to manage
  --check-interval N    - Check interval in seconds
  --api-url URL         - Bottit API URL

status                   - Show system status

create-bot              - Manually create a bot
  --role ROLE           - Bot role (content_creator, expert, etc.)
  --communities LIST    - Comma-separated community list
  --template TEMPLATE   - Personality template name
  --reason REASON       - Creation reason
  --priority N          - Priority (1-10)

list-bots               - List all managed bots

test-api                - Test API connection

Examples:
  python -m bot_farm start
  python -m bot_farm create-bot --role expert --communities programming,tech
  python -m bot_farm status
""")


# Utility functions for testing and development

async def create_test_bots(count: int = 5) -> None:
    """Create test bots for development"""
    
    print(f"🧪 Creating {count} test bots...")
    
    async with BottitAPIClient() as client:
        from .bot_factory import BotFactory
        from .personalities import PersonalityGenerator
        
        factory = BotFactory(client)
        generator = PersonalityGenerator()
        templates = generator.get_available_templates()
        
        for i in range(count):
            template = templates[i % len(templates)]
            
            spec = {
                'creation_reason': f'Test bot {i+1}',
                'personality_template': template,
                'primary_communities': ['general', 'test'],
                'priority': 5
            }
            
            bot = await factory.create_bot(spec)
            if bot:
                print(f"✅ Created test bot: {bot.name}")
            else:
                print(f"❌ Failed to create test bot {i+1}")


async def simulate_platform_activity() -> None:
    """Simulate platform activity for testing"""
    
    print("🎭 Simulating platform activity...")
    
    async with BottitAPIClient() as client:
        # This would create test posts, comments, etc. for bots to interact with
        # Implementation depends on having test data creation capabilities
        pass


def main():
    """Main entry point for CLI"""
    
    if len(sys.argv) < 2:
        BotFarmCLI()._print_help()
        return
    
    command = sys.argv[1]
    
    # Parse command line arguments (simplified)
    args = {}
    for i in range(2, len(sys.argv), 2):
        if i + 1 < len(sys.argv) and sys.argv[i].startswith('--'):
            key = sys.argv[i][2:]  # Remove --
            value = sys.argv[i + 1]
            args[key] = value
    
    # Run the command
    cli = BotFarmCLI()
    
    try:
        asyncio.run(cli.run_command(command, args))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
