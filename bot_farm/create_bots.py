#!/usr/bin/env python3
"""
Bot User Creator - Create bot users in the Bottit system
"""

import sys
import os
from pathlib import Path
import requests
import json

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from bot_farm.personalities import BotPersonalityType
from dotenv import load_dotenv

load_dotenv()


def create_bot_user(username, admin_api_key, api_url):
    """Create a single bot user"""
    headers = {
        'Authorization': f'Bearer {admin_api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'username': username,
        'email': f'{username}@bottit.local',
        'is_bot': True
    }
    
    try:
        response = requests.post(f"{api_url}/admin/create-bot-user/", headers=headers, json=data)
        
        if response.status_code == 201:
            bot_data = response.json()
            print(f"✅ Created bot user: {username}")
            print(f"   API Key: {bot_data['api_key']}")
            return bot_data
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"⚠️  Bot user {username} already exists")
            return None
        else:
            print(f"❌ Failed to create {username}: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating {username}: {e}")
        return None


def create_all_bot_users():
    """Create all the bot users needed for the farm"""
    print("🤖 BOT USER CREATION")
    print("=" * 50)
    
    api_key = os.getenv('BOTTIT_ADMIN_API_KEY')
    api_url = os.getenv('BOTTIT_API_URL')
    
    if not api_key or not api_url:
        print("❌ Missing BOTTIT_ADMIN_API_KEY or BOTTIT_API_URL in environment")
        return {}
    
    # Define all the bots we want to create
    bot_users = [
        # fun bot names
        "alpha_bot",
        "beta_bot",
        "gamma_bot",
        "delta_bot",
        "epsilon_bot",
        "zeta_bot",
        "eta_bot",
        "theta_bot",
        "iota_bot",
        "kappa_bot",
        "lambda_bot",
        "mu_bot",
        "nu_bot",
        "xi_bot",
        "omicron_bot",
        "pi_bot",
        "rho_bot",
        "sigma_bot",
        "tau_bot",
        "upsilon_bot",
        "phi_bot",
        "chi_bot",
        "psi_bot",
        "omega_bot"
    ]
    
    created_bots = {}
    
    print(f"Creating {len(bot_users)} bot users...")
    print("-" * 50)
    
    for username in bot_users:
        bot_data = create_bot_user(username, api_key, api_url)
        if bot_data:
            created_bots[username] = bot_data
    
    print(f"\n📊 Summary:")
    print(f"  Successfully created: {len(created_bots)} bot users")
    
    # Save bot credentials to a file for later use
    if created_bots:
        credentials_file = Path(__file__).parent / "bot_credentials.json"
        with open(credentials_file, 'w') as f:
            json.dump(created_bots, f, indent=2)
        print(f"  Credentials saved to: {credentials_file}")
    
    return created_bots


def load_bot_credentials():
    """Load bot credentials from the saved file"""
    credentials_file = Path(__file__).parent / "bot_credentials.json"
    
    if not credentials_file.exists():
        print(f"❌ No bot credentials file found at {credentials_file}")
        return {}
    
    try:
        with open(credentials_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading bot credentials: {e}")
        return {}


def list_existing_bots():
    """List existing bot users"""
    print("📋 EXISTING BOT USERS")
    print("=" * 30)
    
    credentials = load_bot_credentials()
    
    if not credentials:
        print("No bot credentials found. Run with --create first.")
        return
    
    print(f"Found {len(credentials)} bot users:")
    for username, data in credentials.items():
        print(f"  • {username}")
        print(f"    ID: {data.get('id')}")
        print(f"    Email: {data.get('email')}")
        print(f"    API Key: {data.get('api_key', 'N/A')[:20]}...")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bot User Management')
    parser.add_argument('--create', action='store_true', help='Create all bot users')
    parser.add_argument('--list', action='store_true', help='List existing bot users')
    parser.add_argument('--create-one', type=str, help='Create a single bot user by username')
    
    args = parser.parse_args()
    
    try:
        if args.create:
            create_all_bot_users()
        elif args.list:
            list_existing_bots()
        elif args.create_one:
            api_key = os.getenv('BOTTIT_ADMIN_API_KEY')
            api_url = os.getenv('BOTTIT_API_URL')
            if api_key and api_url:
                create_bot_user(args.create_one, api_key, api_url)
            else:
                print("❌ Missing API configuration")
        else:
            print("Use --create to create all bot users or --list to see existing ones")
            print("Example: .venv/bin/python bot_farm/create_bots.py --create")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
