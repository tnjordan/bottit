#!/usr/bin/env python3
"""
Simple Gemini API test - the absolute basics
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

print("🧪 Testing Gemini API...")

try:
    response = model.generate_content("Write a short post about coding")
    print("✅ SUCCESS! Gemini response:")
    print(response.text)
except Exception as e:
    print(f"❌ Error: {e}")
