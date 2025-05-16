import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Blueprint
from dotenv import load_dotenv
import openai
import re
import logging
from logging.handlers import RotatingFileHandler

# Set up logging with a file handler to ensure logs are written to the file
log_file = os.path.join(os.path.dirname(__file__), 'translations_log.txt')

# Configure root logger
logger = logging.getLogger('radiologytool.app')
logger.setLevel(logging.INFO)

# Create file handler
file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=3)
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)

# Load environment variables from the correct path
dotenv_path = os.path.join(os.path.dirname(__file__), 'key.env')
load_dotenv(dotenv_path)

# Initialize Flask Blueprint instead of app
app = Blueprint('radiology', __name__, 
                template_folder='templates',
                static_folder='static')

# Configure OpenAI with explicit API key - check both direct env var and key.env file
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    logger.error("No OpenAI API key found. Please set the OPENAI_API_KEY in key.env file or as environment variable.")
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY in key.env file or as environment variable.")

# Initialize OpenAI API with the older 0.28.0 style
try:
    # Set the API key globally for the openai module
    openai.api_key = api_key
    logger.info("OpenAI API key set successfully")
except Exception as e:
    logger.error(f"Error setting OpenAI API key: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

# Check for HTTP_PROXY environment variables that might cause issues
http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
if http_proxy or https_proxy:
    logger.warning("HTTP_PROXY or HTTPS_PROXY environment variables are set.")

# Store feedback data
FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), 'feedback_data.json')

def load_feedback():
    """Load feedback from file"""
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_feedback(feedback_data):
    """Save feedback to file"""
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedback_data, f, indent=2)

def format_translation(text):
    """
    Format the translation by adding proper HTML tags and styling.
    """
    # Find the symptoms section
    pattern = r"RELATED SYMPTOMS:(.+?)$"
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        # Split the text into explanation and symptoms
        split_index = text.find("RELATED SYMPTOMS:")
        explanation = text[:split_index].strip()
        symptoms_section = "RELATED SYMPTOMS:" + match.group(1)
        
        # Format bullet points in symptoms section
        symptoms_section = re.sub(r"•\s*([^\n]+)", r"<li>\1</li>", symptoms_section)
        symptoms_section = re.sub(r"\*\s*([^\n]+)", r"<li>\1</li>", symptoms_section)
        symptoms_section = re.sub(r"-\s*([^\n]+)", r"<li>\1</li>", symptoms_section)
        
        # Replace "RELATED SYMPTOMS:" with HTML header
        symptoms_section = symptoms_section.replace("RELATED SYMPTOMS:", 
                                                   "<h5 class='symptoms-header mt-4'>Related Symptoms</h5><ul>")
        symptoms_section += "</ul>"
        
        # Combine formatted parts
        formatted_text = f"<p>{explanation}</p>{symptoms_section}"
        return formatted_text
    else:
        # No symptoms section found, just wrap in paragraph
        return f"<p>{text}</p>"

def translate_radiology_impression(impression):
    """
    Translate technical radiology impression into patient-friendly language
    and identify what symptoms typically match these findings.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are explaining radiology results to a patient who might be worried or confused. "
                                            "Your job is to make complex medical findings easy to understand.\n\n"
                                            "Your response needs to be in TWO sections:\n\n"
                                            "1. First, explain what the findings mean in VERY simple, friendly language at a 6th grade reading level (ages 11-12).\n"
                                            "2. Second, add the heading 'RELATED SYMPTOMS:' and list what symptoms might be connected to these findings.\n\n"
                                            "Guidelines for explanation:\n"
                                            "- Use EXTREMELY simple words a 6th grader would understand\n"
                                            "- Keep sentences short (10-15 words maximum)\n"
                                            "- Use everyday examples when possible (e.g., 'the disc in your back is like a cushion between bones')\n"
                                            "- NEVER use medical terms without explaining them immediately (e.g., 'stenosis, which means narrowing')\n"
                                            "- Be warm and reassuring\n"
                                            "- Use words like 'small,' 'little,' or 'mild' when appropriate to prevent unnecessary worry\n"
                                            "- Keep explanations brief, 3-4 sentences maximum\n\n"
                                            "Guidelines for symptoms:\n"
                                            "- After a clear heading 'RELATED SYMPTOMS:'\n"
                                            "- List 2-3 simple symptoms using bullet points (•)\n"
                                            "- Explain each symptom in VERY simple terms\n"
                                            "- Connect symptoms to the findings using simple cause-effect language"
                },
                {"role": "user", "content": f"Please explain this radiology report in the simplest possible terms that anyone could understand: {impression}"}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # Get the raw text - API response structure is different in v0.28
        raw_text = response.choices[0].message.content
        
        # Format the text with HTML
        formatted_text = format_translation(raw_text)
        
        return formatted_text
    except Exception as e:
        logger.error(f"Error in translation: {str(e)}")
        return f"<p>Error in translation: {str(e)}</p>"

@app.route('/')
def index():
    return render_template('radiology.html')

@app.route('/health')
def health():
    """Health check to verify the blueprint is working"""
    api_key_status = "Available" if os.environ.get("OPENAI_API_KEY") else "Missing"
    return f"Radiology Tool Blueprint is healthy. OpenAI API Key: {api_key_status}"

@app.route('/translate', methods=['POST'])
def translate():
    if request.method == 'POST':
        impression = request.form.get('impression', '')
        
        if not impression:
            return jsonify({'error': 'No impression provided'}), 400
        
        # Create a unique ID for this translation
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        translation_id = f"trans_{timestamp}"
        
        translation = translate_radiology_impression(impression)
        
        # Log the impression and translation
        logger.info(f"TRANSLATION ID: {translation_id}")
        logger.info(f"ORIGINAL: {impression}")
        logger.info(f"TRANSLATION: {translation}")
        logger.info("-" * 80)
        
        # Also directly write to the log file as a backup
        try:
            with open(log_file, 'a') as f:
                f.write(f"\n{datetime.now()} - TRANSLATION ID: {translation_id}\n")
                f.write(f"ORIGINAL: {impression}\n")
                f.write(f"TRANSLATION: {translation}\n")
                f.write("-" * 80 + "\n")
        except Exception as e:
            logger.error(f"Error writing to log file: {e}")
        
        return jsonify({
            'translation': translation,
            'translation_id': translation_id
        })

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """Handle user feedback submission"""
    if request.method == 'POST':
        data = request.json
        
        # Validate required fields
        if not all(key in data for key in ['translation_id', 'original', 'translation', 'rating']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get existing feedback data
        feedback_data = load_feedback()
        
        # Add new feedback with timestamp
        feedback_entry = {
            'id': data['translation_id'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'original_text': data['original'],
            'translation': data['translation'],
            'rating': data['rating'],  # 'thumbs_up' or 'thumbs_down'
            'comment': data.get('comment', '')
        }
        
        feedback_data.append(feedback_entry)
        
        # Save updated feedback data
        save_feedback(feedback_data)
        
        # Log the feedback to the text file
        rating_text = "👍 THUMBS UP" if data['rating'] == 'thumbs_up' else "👎 THUMBS DOWN"
        logger.info(f"FEEDBACK FOR: {data['translation_id']}")
        logger.info(f"RATING: {rating_text}")
        if data.get('comment'):
            logger.info(f"COMMENT: {data.get('comment')}")
        logger.info("-" * 80)
        
        # Also directly write to the log file as a backup
        try:
            with open(log_file, 'a') as f:
                f.write(f"\n{datetime.now()} - FEEDBACK FOR: {data['translation_id']}\n")
                f.write(f"RATING: {rating_text}\n")
                if data.get('comment'):
                    f.write(f"COMMENT: {data.get('comment')}\n")
                f.write("-" * 80 + "\n")
        except Exception as e:
            logger.error(f"Error writing to log file: {e}")
        
        return jsonify({'success': True, 'message': 'Feedback submitted successfully'})

@app.route('/feedback/stats', methods=['GET'])
def feedback_stats():
    """Get feedback statistics - for admin use"""
    feedback_data = load_feedback()
    
    total = len(feedback_data)
    thumbs_up = sum(1 for item in feedback_data if item['rating'] == 'thumbs_up')
    thumbs_down = sum(1 for item in feedback_data if item['rating'] == 'thumbs_down')
    
    return jsonify({
        'total_feedback': total,
        'thumbs_up': thumbs_up,
        'thumbs_down': thumbs_down,
        'approval_rate': (thumbs_up / total) * 100 if total > 0 else 0
    })

@app.route('/view-logs')
def view_logs():
    """View the translation and feedback logs"""
    try:
        # Create log file if it doesn't exist
        if not os.path.exists(log_file):
            try:
                # Make sure the directory exists
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                # Create empty log file with initial message
                with open(log_file, 'w') as f:
                    f.write(f"{datetime.now()} - INFO - Log file created\n")
                    f.write(f"{datetime.now()} - INFO - No translations recorded yet.\n")
                logger.info("Created new log file")
            except Exception as e:
                return render_template('logs.html', log_content=f"<p>Error creating log file: {str(e)}</p>")
        
        # Force a log entry to ensure the file has content
        logger.info("Viewing logs page")
        
        # Read the log file - handle the case where it might be empty
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        if not log_content.strip():
            log_content = "No translations recorded yet."
            # Try to write to the empty file
            with open(log_file, 'w') as f:
                f.write(f"{datetime.now()} - INFO - No translations recorded yet.\n")
        
        # Format the log content with HTML, ensuring proper escaping
        log_content = log_content.replace('\n', '<br>')
        log_content = f'<pre style="white-space: pre-wrap; word-wrap: break-word;">{log_content}</pre>'
        
        return render_template('logs.html', log_content=log_content)
    except Exception as e:
        error_message = f"<p>Error reading log file: {str(e)}</p>"
        # Try to log the error
        try:
            logger.error(f"Error in view_logs: {str(e)}")
        except:
            pass
        return render_template('logs.html', log_content=error_message)

# Only run as standalone if script is executed directly
if __name__ == '__main__':
    # Create a Flask app for standalone mode
    standalone_app = Flask(__name__)
    standalone_app.register_blueprint(app)
    standalone_app.run(host='0.0.0.0', port=8080, debug=True) 