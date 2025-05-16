#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from app import app

# Load environment variables from key.env file
dotenv_path = os.path.join(os.path.dirname(__file__), 'key.env')
load_dotenv(dotenv_path)

# Set OpenAI API key from environment variable
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("\nNo OpenAI API key found in environment variables.")
    print("Make sure OPENAI_API_KEY is set in key.env file.")
    exit(1)

# Run the app
print("\nStarting Radiology Translator app...")
print("Access the app at: http://127.0.0.1:8080")
print("Press CTRL+C to quit")

app.run(host='127.0.0.1', port=8080, debug=True) 