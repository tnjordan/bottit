#!/usr/bin/env python3
"""
Debug what organizer is returning
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_farm.organizer import BotFarmOrganizer

def debug_organizer():
    print("🔍 Debugging organizer output...")
    
    organizer = BotFarmOrganizer()
    available_posts, available_comments = organizer.fetch_available_content()
    
    print(f"Type of available_posts: {type(available_posts)}")
    print(f"Length: {len(available_posts) if hasattr(available_posts, '__len__') else 'N/A'}")
    print(f"Content: {available_posts}")
    
    print(f"\nType of available_comments: {type(available_comments)}")
    print(f"Length: {len(available_comments) if hasattr(available_comments, '__len__') else 'N/A'}")
    print(f"Content: {available_comments}")

if __name__ == "__main__":
    debug_organizer()
