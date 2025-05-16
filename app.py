from flask import Flask, render_template, redirect, url_for
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add radiologytool to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'radiologytool'))

app = Flask(__name__)

@app.route('/')
def index():
    """Main landing page that shows all available tools"""
    tools = [
        {
            'name': 'Radiology Tool',
            'description': 'Translates technical radiology impressions into patient-friendly language',
            'url': '/radiology',
            'icon': 'medical.svg'
        }
        # Add more tools here as they become available
    ]
    return render_template('index.html', tools=tools)

@app.route('/radiology')
def radiology_redirect():
    """Redirect to the radiology tool"""
    return redirect('/radiology/')

# Debug route to check if the app is running
@app.route('/debug')
def debug():
    """Debug endpoint to verify the application is running"""
    return "App is running. Registered blueprints: " + ", ".join([bp.name for bp in app.blueprints.values()])

try:
    # Import the radiologytool module
    import radiologytool.app
    logger.info("Successfully imported radiologytool.app module")
    
    # Explicitly verify the blueprint exists
    if not hasattr(radiologytool.app, 'app'):
        logger.error("radiologytool.app module does not have an 'app' blueprint")
        raise AttributeError("radiologytool.app module does not have an 'app' blueprint")
        
    # Mount the radiology tool app
    app.register_blueprint(radiologytool.app.app, url_prefix='/radiology')
    logger.info("Successfully registered radiologytool blueprint")
except Exception as e:
    logger.error(f"Error registering radiologytool blueprint: {e}")
    # Add stack trace for better debugging
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    try:
        logger.info("Starting application...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error starting application: {e}") 