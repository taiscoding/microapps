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
    Also removes any remaining conversational lead-ins and ensures
    technical terms have explanations in parentheses.
    """
    # Remove common conversational lead-ins
    lead_ins = [
        "sure!", "sure,", "absolutely!", "absolutely,", "here's", "i can help", "i'll explain",
        "let me explain", "let's break this down", "to put it simply", "in simple terms",
        "the report shows", "this means that", "this indicates that", "based on the report",
        "the radiology report indicates", "the findings show", "the findings indicate",
    ]
    
    # Clean up text by removing conversational starts
    lower_text = text.lower()
    first_sentence_end = lower_text.find('.')
    if first_sentence_end > 0:
        first_sentence = lower_text[:first_sentence_end]
        for lead_in in lead_ins:
            if lead_in in first_sentence:
                # Remove the lead-in phrase and any text before it
                start_pos = text.lower().find(lead_in)
                end_pos = start_pos + len(lead_in)
                # Skip to the next non-space character after the lead-in
                while end_pos < len(text) and (text[end_pos].isspace() or text[end_pos] in ',:;'):
                    end_pos += 1
                text = text[end_pos:]
                # Capitalize the first letter
                if text:
                    text = text[0].upper() + text[1:]
                break
    
    # First, clean up any problematic or nested explanations that might already exist
    # This pattern looks for text like "L4 (whiL5 (which is..." and fixes it
    nested_pattern = r'([A-Z][0-9])(\s*\(\s*whi[A-Z][0-9]\s*\()'
    text = re.sub(nested_pattern, r'\1 (', text)
    
    # Add a general cleanup for any incorrectly nested parentheses
    while re.search(r'\([^()]*\([^()]*\)[^()]*\)', text):
        text = re.sub(r'\(([^()]*)\(([^()]*)\)([^()]*)\)', r'(\1\2\3)', text)
    
    # Special case for vertebral levels that appear together (like "L4-L5")
    # Replace them with a combined explanation instead of individual ones
    for pattern, replacement in [
        (r'L([1-5])[- ]L([1-5])', r'L\1-L\2 (the lower part of your back)'),
        (r'T([1-9][0-2]?)[- ]T([1-9][0-2]?)', r'T\1-T\2 (the middle part of your back)'),
        (r'C([1-7])[- ]C([1-7])', r'C\1-C\2 (the neck area)')
    ]:
        # Only replace if not already followed by an explanation
        combined_pattern = pattern + r'(?!\s*\()'
        text = re.sub(combined_pattern, replacement, text)
    
    # Import the medical terms dictionary from utils
    from radiologytool.utils import COMMON_MEDICAL_TERMS
    
    # Create a helper function to check if a term already has an explanation
    def has_explanation(term, text):
        # This regex looks for the term followed by an opening parenthesis within a reasonable distance
        pattern = re.escape(term) + r'\s*\([^)]*\)'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    # Ensure every medical term has an explanation in parentheses if not already present
    for term, explanation in COMMON_MEDICAL_TERMS.items():
        # Check if the term is a standalone word and doesn't already have an explanation
        term_pattern = r'\b' + re.escape(term) + r'\b(?!\s*[\(\{])'
        if re.search(term_pattern, text, re.IGNORECASE) and not has_explanation(term, text):
            # The term exists without an explanation in parentheses
            replacement = f"{term} (which means {explanation})"
            text = re.sub(term_pattern, replacement, text, flags=re.IGNORECASE)
    
    # Common anatomical locations and terms dictionary
    anatomical_terms = {
        # Spine - these are handled separately above for the combined cases
        r'\bL[1-5]\b': 'a vertebra in the lower back',
        r'\bT[1-9][0-2]?\b': 'a vertebra in the middle back',
        r'\bC[1-7]\b': 'a vertebra in the neck',
        r'\bS[1-5]\b': 'part of the sacrum (base of the spine)',
        
        # Brain
        r'\bfrontal lobe\b': 'the front part of the brain that controls thinking and movement',
        r'\btemporal lobe\b': 'the side part of the brain that helps with hearing and memory',
        r'\bparietal lobe\b': 'the top part of the brain that processes sensations',
        r'\boccipital lobe\b': 'the back part of the brain that processes vision',
        r'\bcerebellum\b': 'the lower back part of the brain that controls balance and coordination',
        r'\bbrainstem\b': 'the part that connects the brain to the spinal cord and controls basic functions like breathing',
        
        # Chest
        r'\bpulmonary\b': 'related to the lungs',
        r'\baorta\b': 'the main blood vessel carrying blood from your heart',
        r'\bventricle\b': 'a chamber of the heart',
        r'\batrium\b': 'an upper chamber of the heart',
        r'\bbronch(i|us)\b': 'the airways in the lungs',
        
        # Abdomen
        r'\bhepatobiliary\b': 'related to the liver and bile ducts',
        r'\bpancreas\b': 'an organ behind your stomach that helps with digestion',
        r'\bspleen\b': 'an organ near your stomach that helps fight infection',
        r'\bkidney\b': 'an organ that filters waste from your blood',
        r'\bgallbladder\b': 'an organ that stores bile from your liver to help with digestion',
        r'\bcolon\b': 'the large intestine',
        
        # Common conditions
        r'\batrophy\b': 'shrinkage',
        r'\bhypertrophy\b': 'enlargement',
        r'\bstenosis\b': 'narrowing',
        r'\binfarct\b': 'an area of damaged tissue due to lack of blood flow',
        r'\blesion\b': 'an abnormal area of tissue',
        r'\bnodule\b': 'a small rounded lump',
        r'\beffusion\b': 'a buildup of fluid',
        r'\bedema\b': 'swelling due to excess fluid',
        r'\bhemorrhage\b': 'bleeding',
        r'\bischemia\b': 'reduced blood flow'
    }
    
    # Add explanations to anatomical terms not already explained
    for term_pattern, explanation in anatomical_terms.items():
        # Only match if not followed by parentheses and not already explained elsewhere
        matches = re.finditer(term_pattern + r'(?!\s*[\(\{])', text, re.IGNORECASE)
        for match in matches:
            term = match.group(0)
            if not has_explanation(term, text):
                replacement = f"{term} ({explanation})"
                # Replace only this exact instance
                text = text[:match.start()] + replacement + text[match.end():]
    
    # Do a final check for any nested parentheses that might have been introduced
    while re.search(r'\([^()]*\([^()]*\)[^()]*\)', text):
        text = re.sub(r'\(([^()]*)\(([^()]*)\)([^()]*)\)', r'(\1\2\3)', text)
    
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
    at a 6th grade reading level, without mentioning symptoms.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You explain radiology results in simple, clear language for patients with no medical background. "
                                            "Your job is to translate complex medical impressions into one cohesive, easily understandable explanation.\n\n"
                                            "CRITICAL REQUIREMENTS:\n"
                                            "1. Create ONE SINGLE PARAGRAPH that explains ONLY the medical impression.\n"
                                            "2. DO NOT mention symptoms, causes, risk factors, or treatments - focus ONLY on what the impression means.\n"
                                            "3. DO NOT use bullet points, asterisks, or any special formatting.\n"
                                            "4. Start directly with the explanation - no introductory phrases.\n\n"
                                            "EXAMPLE FORMAT:\n"
                                            "\"There is some mild wear and tear in the disc between two bones in the lower part of your back (called L4–L5). The disc is bulging a little and making the space where your nerves pass through a bit tighter, especially on the left side.\"\n\n"
                                            "GUIDELINES:\n"
                                            "- Use short, clear sentences at a 6th grade reading level.\n"
                                            "- DO NOT include any information about symptoms or possible symptoms.\n"
                                            "- DO NOT include any information about causes, risk factors, or treatments.\n"
                                            "- When mentioning technical terms, always include simple explanations in parentheses.\n"
                                            "- For vertebral levels (like L4-L5), use a consistent description: \"L4-L5 (the area in your lower back)\"\n"
                                            "- Keep your response concise, clear, and reassuring.\n"
                                            "- Always prioritize simple, direct language for a patient with no medical background."
                },
                {"role": "user", "content": f"Explain this radiology report impression in simple terms, focusing ONLY on what the findings mean (not symptoms, causes, risk factors, or treatments): {impression}"}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # Get the response text from the new API structure
        raw_text = response.choices[0].message.content
        
        # Always use format_single_paragraph rather than format_translation
        formatted_text = format_single_paragraph(raw_text)
        
        return formatted_text
    except Exception as e:
        logger.error(f"Error in translation: {str(e)}")
        return f"<p>Error in translation: {str(e)}</p>"

def format_single_paragraph(text):
    """
    Format the translation as a single paragraph with HTML tags.
    Also removes any remaining conversational lead-ins and ensures
    technical terms have explanations in parentheses.
    """
    # Remove common conversational lead-ins
    lead_ins = [
        "sure!", "sure,", "absolutely!", "absolutely,", "here's", "i can help", "i'll explain",
        "let me explain", "let's break this down", "to put it simply", "in simple terms",
        "the report shows", "this means that", "this indicates that", "based on the report",
        "the radiology report indicates", "the findings show", "the findings indicate",
    ]
    
    # Clean up text by removing conversational starts
    lower_text = text.lower()
    first_sentence_end = lower_text.find('.')
    if first_sentence_end > 0:
        first_sentence = lower_text[:first_sentence_end]
        for lead_in in lead_ins:
            if lead_in in first_sentence:
                # Remove the lead-in phrase and any text before it
                start_pos = text.lower().find(lead_in)
                end_pos = start_pos + len(lead_in)
                # Skip to the next non-space character after the lead-in
                while end_pos < len(text) and (text[end_pos].isspace() or text[end_pos] in ',:;'):
                    end_pos += 1
                text = text[end_pos:]
                # Capitalize the first letter
                if text:
                    text = text[0].upper() + text[1:]
                break
    
    # First, clean up any problematic or nested explanations that might already exist
    # This pattern looks for text like "L4 (whiL5 (which is..." and fixes it
    nested_pattern = r'([A-Z][0-9])(\s*\(\s*whi[A-Z][0-9]\s*\()'
    text = re.sub(nested_pattern, r'\1 (', text)
    
    # Add a general cleanup for any incorrectly nested parentheses
    while re.search(r'\([^()]*\([^()]*\)[^()]*\)', text):
        text = re.sub(r'\(([^()]*)\(([^()]*)\)([^()]*)\)', r'(\1\2\3)', text)
    
    # Special case for vertebral levels that appear together (like "L4-L5")
    # Replace them with a combined explanation instead of individual ones
    for pattern, replacement in [
        (r'L([1-5])[- ]L([1-5])', r'L\1-L\2 (the area in your lower back)'),
        (r'T([1-9][0-2]?)[- ]T([1-9][0-2]?)', r'T\1-T\2 (the area in your middle back)'),
        (r'C([1-7])[- ]C([1-7])', r'C\1-C\2 (the area in your neck)')
    ]:
        # Only replace if not already followed by an explanation
        combined_pattern = pattern + r'(?!\s*\()'
        text = re.sub(combined_pattern, replacement, text)
    
    # Import the medical terms dictionary from utils
    from radiologytool.utils import COMMON_MEDICAL_TERMS
    
    # Create a helper function to check if a term already has an explanation
    def has_explanation(term, text):
        # This regex looks for the term followed by an opening parenthesis within a reasonable distance
        pattern = re.escape(term) + r'\s*\([^)]*\)'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    # Ensure every medical term has an explanation in parentheses if not already present
    for term, explanation in COMMON_MEDICAL_TERMS.items():
        # Check if the term is a standalone word and doesn't already have an explanation
        term_pattern = r'\b' + re.escape(term) + r'\b(?!\s*[\(\{])'
        if re.search(term_pattern, text, re.IGNORECASE) and not has_explanation(term, text):
            # The term exists without an explanation in parentheses
            replacement = f"{term} ({explanation})"
            text = re.sub(term_pattern, replacement, text, flags=re.IGNORECASE)
    
    # Common anatomical locations and terms dictionary
    anatomical_terms = {
        # Spine - treat individual vertebrae consistently
        r'\bL[1-5]\b': 'part of your lower back',
        r'\bT[1-9][0-2]?\b': 'part of your middle back',
        r'\bC[1-7]\b': 'part of your neck',
        r'\bS[1-5]\b': 'part of the base of your spine',
        
        # Brain
        r'\bfrontal lobe\b': 'the front part of the brain that controls thinking and movement',
        r'\btemporal lobe\b': 'the side part of the brain that helps with hearing and memory',
        r'\bparietal lobe\b': 'the top part of the brain that processes sensations',
        r'\boccipital lobe\b': 'the back part of the brain that processes vision',
        r'\bcerebellum\b': 'the lower back part of the brain that controls balance and coordination',
        r'\bbrainstem\b': 'the part that connects the brain to the spinal cord and controls basic functions like breathing',
        
        # Chest
        r'\bpulmonary\b': 'related to the lungs',
        r'\baorta\b': 'the main blood vessel carrying blood from your heart',
        r'\bventricle\b': 'a chamber of the heart',
        r'\batrium\b': 'an upper chamber of the heart',
        r'\bbronch(i|us)\b': 'the airways in the lungs',
        
        # Abdomen
        r'\bhepatobiliary\b': 'related to the liver and bile ducts',
        r'\bpancreas\b': 'an organ behind your stomach that helps with digestion',
        r'\bspleen\b': 'an organ near your stomach that helps fight infection',
        r'\bkidney\b': 'an organ that filters waste from your blood',
        r'\bgallbladder\b': 'an organ that stores bile from your liver to help with digestion',
        r'\bcolon\b': 'the large intestine',
        
        # Common conditions
        r'\batrophy\b': 'shrinkage',
        r'\bhypertrophy\b': 'enlargement',
        r'\bstenosis\b': 'narrowing',
        r'\binfarct\b': 'an area of damaged tissue due to lack of blood flow',
        r'\blesion\b': 'an abnormal area of tissue',
        r'\bnodule\b': 'a small rounded lump',
        r'\beffusion\b': 'a buildup of fluid',
        r'\bedema\b': 'swelling due to excess fluid',
        r'\bhemorrhage\b': 'bleeding',
        r'\bischemia\b': 'reduced blood flow'
    }
    
    # Add explanations to anatomical terms not already explained
    for term_pattern, explanation in anatomical_terms.items():
        # Only match if not followed by parentheses and not already explained elsewhere
        matches = re.finditer(term_pattern + r'(?!\s*[\(\{])', text, re.IGNORECASE)
        for match in matches:
            term = match.group(0)
            if not has_explanation(term, text):
                replacement = f"{term} ({explanation})"
                # Replace only this exact instance
                text = text[:match.start()] + replacement + text[match.end():]
    
    # Do a final check for any nested parentheses that might have been introduced
    while re.search(r'\([^()]*\([^()]*\)[^()]*\)', text):
        text = re.sub(r'\(([^()]*)\(([^()]*)\)([^()]*)\)', r'(\1\2\3)', text)
    
    # Clean up any asterisks, stars, or bullet points
    text = re.sub(r'\*+', '', text)       # Remove asterisks
    text = re.sub(r'•', '', text)         # Remove bullet points
    text = re.sub(r'^\s*-\s*', '', text)  # Remove hyphens used as bullets
    
    # Remove any mention of symptoms, causes, treatments, or risk factors
    symptom_patterns = [
        r'(?i)related symptoms[:\s]*.*$',
        r'(?i)this can cause[^\.]*\.',
        r'(?i)symptoms may include[^\.]*\.',
        r'(?i)you might (feel|experience)[^\.]*\.',
        r'(?i)this (may|might|can) lead to[^\.]*\.',
        r'(?i)common symptoms[^\.]*\.',
        r'(?i)you (may|might|can) feel[^\.]*\.',
        r'(?i)you (may|might|can) notice[^\.]*\.',
        r'(?i)this could result in[^\.]*\.',
        r'(?i)this is (often|sometimes|usually) associated with[^\.]*\.',
        r'(?i)patients (often|sometimes|usually) experience[^\.]*\.',
        r'(?i)treatment (options|may|might|includes|involves)[^\.]*\.',
        r'(?i)risk factors[^\.]*\.',
        r'(?i)causes (of|for|include)[^\.]*\.'
    ]
    
    for pattern in symptom_patterns:
        text = re.sub(pattern, '', text)
    
    # Remove any bullet list sections that might appear in the text
    bullet_list_pattern = r'(?:\s*[•\*-]\s*[^\n]+\n?)+'
    text = re.sub(bullet_list_pattern, ' ', text)
    
    # Clean up multiple spaces and ensure proper sentence spacing
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\.\s+', '. ', text)
    
    # Final check for any trailing symbols
    text = text.rstrip('*• \t\n-')
    
    # Wrap in paragraph tags
    return f"<p>{text}</p>"

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
    
    # Register the blueprint without a URL prefix for standalone mode
    standalone_app.register_blueprint(app)
    
    standalone_app.run(host='0.0.0.0', port=8080, debug=True) 