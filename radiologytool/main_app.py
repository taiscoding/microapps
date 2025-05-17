from flask import Flask
from radiologytool.app import app as radiologyapp

# Create the main Flask application
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

# Register the radiology blueprint without a prefix
# This ensures routes like /translate work directly
app.register_blueprint(radiologyapp)

# Set up Jinja context processor for template variables
@app.context_processor
def inject_globals():
    """Inject global variables into templates"""
    from datetime import datetime
    return {
        'current_year': datetime.now().year,
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True) 