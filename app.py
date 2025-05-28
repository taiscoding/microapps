from flask import Flask, render_template, redirect, url_for
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'radiologytool'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'lab_value_helper'))

app = Flask(__name__)

# Add a context processor to make 'now' available in all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/')
def index():
    """Main landing page that shows all available tools"""
    tools = [
        {
            'name': 'Medical Report Helper',
            'description': 'Turns medical reports into simple language anyone can understand',
            'url': '/radiology',
            'icon': 'medical.svg'
        },
        {
            'name': 'Lab Value Helper',
            'description': 'Clinical significance engine that reduces alert fatigue by showing what lab values actually matter',
            'url': '/lab-value-helper',
            'icon': 'flask'
        }
        # Add more tools here as they become available
    ]
    return render_template('index.html', tools=tools)

@app.route('/radiology')
def radiology_redirect():
    """Redirect to the radiology tool"""
    return redirect('/radiology/')

@app.route('/lab-value-helper')
def lab_helper_redirect():
    """Redirect to the lab value helper tool"""
    return redirect('/lab-value-helper/')

# Debug route to check if the app is running
@app.route('/debug')
def debug():
    """Debug endpoint to verify the application is running"""
    return "App is running. Registered blueprints: " + ", ".join([bp.name for bp in app.blueprints.values()])

# Register radiologytool blueprint
try:
    import radiologytool.app
    logger.info("Successfully imported radiologytool.app module")
    
    if not hasattr(radiologytool.app, 'app'):
        logger.error("radiologytool.app module does not have an 'app' blueprint")
        raise AttributeError("radiologytool.app module does not have an 'app' blueprint")
        
    app.register_blueprint(radiologytool.app.app, url_prefix='/radiology')
    logger.info("Successfully registered radiologytool blueprint")
except Exception as e:
    logger.error(f"Error registering radiologytool blueprint: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")

# Register lab value helper blueprint
try:
    import lab_value_helper.app
    logger.info("Successfully imported lab_value_helper.app module")
    
    app.register_blueprint(lab_value_helper.app.app, url_prefix='/lab-value-helper')
    logger.info("Successfully registered lab_value_helper blueprint")
except Exception as e:
    logger.error(f"Error registering lab_value_helper blueprint: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    try:
        logger.info("Starting application...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error starting application: {e}") 