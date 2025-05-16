# MicroApps Hub

A centralized hosting application that provides access to various tools and utilities.

## Currently Available Tools

1. **Radiology Tool** - Translates technical radiology impressions into patient-friendly language

## Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key:
   ```
   cp radiologytool/key.env.example radiologytool/key.env
   ```
   Then edit the `radiologytool/key.env` file to add your API key.
   
   **IMPORTANT:** Never commit the key.env file with your real API key.
   
4. Run the application:
   ```
   python run.py
   ```
5. Open your browser and navigate to `http://localhost:5001`

## Setting Up as a New Git Repository

If you want to create a fresh Git repository with this code:

1. Delete the existing `.git` directory (if present):
   ```
   rm -rf .git
   ```

2. Initialize a new Git repository:
   ```
   git init
   ```

3. Make your first commit:
   ```
   git add .
   git commit -m "Initial commit"
   ```

4. Add your remote repository:
   ```
   git remote add origin your-repository-url
   ```

5. Push to your repository:
   ```
   git push -u origin main
   ```

## Adding New Tools

To add a new tool to the hub:

1. Create a new directory for your tool
2. Implement the tool as a Flask Blueprint
3. Add the tool to the main app.py file:
   - Import the Blueprint
   - Register the Blueprint with a URL prefix
   - Add the tool to the tools list in the index() function

## Development

Each tool can be developed and tested independently. For example, to run just the radiology tool:

```
cd radiologytool
python app.py
```

## Requirements

- Python 3.8+
- Flask
- Other requirements specified in requirements.txt 