import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure radiologytool has required files
radiologytool_dir = os.path.join(os.path.dirname(__file__), 'radiologytool')
key_env_path = os.path.join(radiologytool_dir, 'key.env')

# Create key.env file if it doesn't exist
if not os.path.exists(key_env_path):
    logger.info(f"Creating empty key.env file for deployment at {key_env_path}")
    try:
        os.makedirs(os.path.dirname(key_env_path), exist_ok=True)
        with open(key_env_path, 'w') as f:
            f.write(f"# This file is automatically created for deployment\n")
            f.write(f"# The actual API key should be set in environment variables\n")
            f.write(f"FLASK_APP=app.py\n")
            f.write(f"FLASK_ENV=production\n")
    except Exception as e:
        logger.error(f"Failed to create key.env file: {e}")

# Import and run the main app
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port) 