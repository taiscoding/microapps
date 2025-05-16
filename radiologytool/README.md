# Radiology Translator

A web-based tool that translates technical radiology impressions into patient-friendly language using AI.

## Features

- Convert medical jargon into plain, easy-to-understand language
- Web interface for easy access
- Sample radiology impressions for testing
- Mobile-friendly responsive design

## Requirements

- Python 3.7+
- OpenAI API key

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/radiology-translator.git
   cd radiology-translator
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   FLASK_APP=app.py
   FLASK_ENV=development
   ```

## Usage

1. Start the application:
   ```
   python3 run.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:8080
   ```

3. Paste a radiology impression into the text area and click "Translate"

## How It Works

The application uses OpenAI's GPT model to analyze medical terminology and convert it into simplified language that patients can understand. The system has been prompted to:

- Explain medical terms in plain language
- Be reassuring but honest about findings
- Avoid medical jargon
- Provide context for medical conditions

## Limitations

- This tool is for educational purposes only
- Always consult with healthcare providers about medical reports
- The AI may occasionally misinterpret complex medical terminology
- Not a substitute for professional medical advice

## License

MIT

## Acknowledgements

- OpenAI for providing the API used for translation
- Flask for the web framework 