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
    logger.info(f"Creating key.env file for deployment at {key_env_path}")
    try:
        os.makedirs(os.path.dirname(key_env_path), exist_ok=True)
        openai_api_key = os.environ.get('OPENAI_API_KEY', '')
        with open(key_env_path, 'w') as f:
            f.write(f"# This file is automatically created for deployment\n")
            f.write(f"# The actual API key should be set in environment variables\n")
            f.write(f"FLASK_APP=app.py\n")
            f.write(f"FLASK_ENV=production\n")
            # Write the API key if it exists in environment
            if openai_api_key:
                f.write(f"OPENAI_API_KEY={openai_api_key}\n")
    except Exception as e:
        logger.error(f"Failed to create key.env file: {e}")

# Set OpenAI API key in environment before importing app
if 'OPENAI_API_KEY' in os.environ:
    logger.info("OpenAI API key found in environment variables")
    # Ensure it's explicitly set in os.environ for child processes
    os.environ['OPENAI_API_KEY'] = os.environ['OPENAI_API_KEY']
else:
    logger.error("No OpenAI API key found in environment variables. The application will likely fail.")

# Configure OpenAI with v1.0+ API
try:
    # Just verify we can import the OpenAI module
    # The actual client will be created in the app when needed
    from openai import OpenAI
    logger.info("Successfully verified OpenAI module is available")
except Exception as e:
    logger.error(f"Failed to import OpenAI module: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")

# Add radiologytool to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'radiologytool'))

try:
    # Import and run the main app
    from app import app
    logger.info("Successfully imported app")
except Exception as e:
    logger.error(f"Error importing app: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 10000))
        logger.info(f"Starting application on port {port}")
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1) 