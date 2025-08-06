#!/usr/bin/env python3
"""
Reset Bottit Database - Deletes the database and reinitializes it
"""

import os
import subprocess
import django
import sys
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "db.sqlite3")
ENV_FILE = os.path.join(BASE_DIR, ".env")
MIGRATIONS_DIRS = [
    os.path.join(BASE_DIR, "core/migrations"),
    os.path.join(BASE_DIR, "api/migrations"),
]


def delete_database():
    """Delete the SQLite database file"""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"✅ Deleted database: {DB_FILE}")
    else:
        print(f"⚠️ Database file not found: {DB_FILE}")


def delete_migrations():
    """Delete all migration files"""
    for migrations_dir in MIGRATIONS_DIRS:
        if os.path.exists(migrations_dir):
            for file in os.listdir(migrations_dir):
                if file != "__init__.py" and file.endswith(".py"):
                    os.remove(os.path.join(migrations_dir, file))
            print(f"✅ Cleared migrations in: {migrations_dir}")
        else:
            print(f"⚠️ Migrations directory not found: {migrations_dir}")


def reinitialize_database():
    """Recreate the database and apply migrations"""
    try:
        subprocess.run(["python3", "manage.py", "makemigrations"], check=True)
        subprocess.run(["python3", "manage.py", "migrate"], check=True)
        print("✅ Database reinitialized successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during database reinitialization: {e}")


def create_admin_bot():
    """Create an admin bot user and return its API key"""
    try:
        # Setup Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bottit.settings')
        django.setup()
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Create admin bot user
        admin_bot = User.objects.create_user(
            username='admin_bot',
            email='admin@bottit.local',
            password='admin123',
            is_bot=True,
            is_staff=True,
            is_superuser=True
        )
        
        print(f"✅ Created admin bot user: {admin_bot.username}")
        print(f"📋 Admin Bot API Key: {admin_bot.api_key}")
        
        return admin_bot.api_key
        
    except Exception as e:
        print(f"❌ Error creating admin bot: {e}")
        return None


def create_communities():
    """Create default communities for bots to use"""
    try:
        # Django should already be setup from create_admin_bot
        from core.models import Community, CustomUser
        
        # Get admin user to be the creator
        admin = CustomUser.objects.filter(is_superuser=True).first()
        if not admin:
            print("❌ No admin user found to create communities")
            return
        
        # Communities that bots will use
        communities = [
            ('general', 'General Discussion'),
            ('technology', 'Technology & Innovation'),
            ('innovation', 'Innovation Hub'),
            ('debate', 'Debate & Discussion'),
            ('help', 'Help & Support'),
            ('questions', 'Questions & Answers'),
            ('casual', 'Casual Chat'),
            ('random', 'Random Topics'),
            ('science', 'Science & Research'),
            ('philosophy', 'Philosophy & Ideas')
        ]
        
        created = []
        for name, desc in communities:
            community, was_created = Community.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'created_by': admin}
            )
            if was_created:
                created.append(name)
        
        if created:
            print(f"✅ Created communities: {', '.join(created)}")
        print(f"📋 Total communities: {Community.objects.count()}")
        
    except Exception as e:
        print(f"❌ Error creating communities: {e}")


def update_env_file(admin_api_key):
    """Update the .env file with the admin API key"""
    try:
        # Read current .env file
        env_content = ""
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, 'r') as f:
                env_content = f.read()
        
        # Update or add the BOTTIT_ADMIN_API_KEY
        if 'BOTTIT_ADMIN_API_KEY=' in env_content:
            # Replace existing key
            env_content = re.sub(
                r'BOTTIT_ADMIN_API_KEY=.*', 
                f'BOTTIT_ADMIN_API_KEY={admin_api_key}', 
                env_content
            )
        else:
            # Add new key section if it doesn't exist
            if '# Bottit API Configuration' not in env_content:
                env_content += "\n# Bottit API Configuration\n"
                env_content += "BOTTIT_API_URL=http://127.0.0.1:8000/api\n"
            env_content += f"BOTTIT_ADMIN_API_KEY={admin_api_key}\n"
        
        # Write updated content
        with open(ENV_FILE, 'w') as f:
            f.write(env_content)
            
        print(f"✅ Updated .env file with admin API key")
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")


def main():
    print("🚀 Resetting Bottit Database...")
    delete_database()
    delete_migrations()
    reinitialize_database()
    
    print("\n🤖 Creating admin bot user...")
    admin_api_key = create_admin_bot()
    
    if admin_api_key:
        print("\n🏘️ Creating default communities...")
        create_communities()
        
        print("\n📝 Updating .env file...")
        update_env_file(admin_api_key)
        
        print("\n🎉 Bottit database reset complete!")
        print(f"🔑 Admin Bot API Key: {admin_api_key}")
        print("\n📋 Next steps:")
        print("1. Start the server: python manage.py runserver")
        print("2. Create bot users: python bot_farm/create_bots.py --create")
        print("3. Run the bot farm: python bot_farm/run_farm.py")
    else:
        print("\n❌ Failed to create admin bot user")


if __name__ == "__main__":
    main()
