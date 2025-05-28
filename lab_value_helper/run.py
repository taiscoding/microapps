#!/usr/bin/env python3
"""
Flask application runner for Lab Value Helper
"""

from flask import Flask
from app import app as lab_value_helper_blueprint

# Create the main Flask application
flask_app = Flask(__name__)

# Register the lab value helper blueprint
flask_app.register_blueprint(lab_value_helper_blueprint, url_prefix='/lab-value-helper')

# Add a root route that redirects to the lab helper
@flask_app.route('/')
def index():
    return flask_app.redirect('/lab-value-helper/')

if __name__ == '__main__':
    print("🧪 Starting Lab Value Helper - Clinical Significance Engine")
    print("📍 Access the application at: http://localhost:5001")
    print("🔬 Direct link: http://localhost:5001/lab-value-helper/")
    print("=" * 60)
    flask_app.run(debug=True, host='0.0.0.0', port=5001) 