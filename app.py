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

try:
    # Import the radiologytool module
    import radiologytool.app 
    # Mount the radiology tool app
    app.register_blueprint(radiologytool.app.app, url_prefix='/radiology')
    logger.info("Successfully registered radiologytool blueprint")
except Exception as e:
    logger.error(f"Error registering radiologytool blueprint: {e}")

if __name__ == '__main__':
    try:
        logger.info("Starting application...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error starting application: {e}") 