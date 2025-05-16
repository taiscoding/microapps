#!/usr/bin/env python3
"""
Run script for the MicroApps Hub

This script starts the MicroApps Hub application.
"""

import os
from dotenv import load_dotenv
from app import app

# Load environment variables from the key.env file in radiologytool directory
dotenv_path = os.path.join(os.path.dirname(__file__), 'radiologytool', 'key.env')
load_dotenv(dotenv_path)

# Check if OpenAI API key is set
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Warning: No OpenAI API key found in environment variables.")
    print("Make sure OPENAI_API_KEY is set in radiologytool/key.env file.")

if __name__ == '__main__':
    print("Starting MicroApps Hub server...")
    print("Access the app at: http://localhost:5001")
    print("Press CTRL+C to quit")
    app.run(debug=True, host='0.0.0.0', port=5001) 